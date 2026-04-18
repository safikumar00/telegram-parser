"""Telethon-backed fetcher with flood-wait handling + incremental sync."""
from __future__ import annotations

import asyncio
from datetime import datetime
from typing import AsyncIterator

from ..logging_setup import get_logger
from ..storage.models import Group, Message
from .base import FetchOptions, MessageFetcher

log = get_logger(__name__)


class TelethonFetcher(MessageFetcher):
    """Wraps Telethon's TelegramClient. Connection is lazy so the rest of the
    pipeline can be imported without the telethon runtime penalty."""

    def __init__(
        self,
        api_id: int,
        api_hash: str,
        phone: str,
        session_name: str = "intelligence",
        rate_limit_sleep: float = 1.0,
    ) -> None:
        self._api_id = api_id
        self._api_hash = api_hash
        self._phone = phone
        self._session_name = session_name
        self._sleep = rate_limit_sleep
        self._client = None  # TelegramClient

    async def connect(self) -> None:
        if self._client is not None:
            return
        # Import inside method so projects without telethon installed still load.
        from telethon import TelegramClient  # type: ignore

        self._client = TelegramClient(
            self._session_name, self._api_id, self._api_hash
        )
        log.info(
            "telethon connecting",
            extra={
                "session": self._session_name,
                "phone": self._phone,
                "hint": (
                    "first run: Telegram will send a login code — run this "
                    "command in an INTERACTIVE terminal, or pre-create the "
                    "session with `python -m scripts.list_groups` once."
                ),
            },
        )
        await self._client.start(phone=self._phone)  # type: ignore[func-returns-value]
        me = await self._client.get_me()  # type: ignore[attr-defined]
        log.info(
            "telethon connected",
            extra={
                "session": self._session_name,
                "as_user": getattr(me, "username", None) or getattr(me, "id", "?"),
            },
        )

    async def disconnect(self) -> None:
        if self._client is not None:
            await self._client.disconnect()  # type: ignore[func-returns-value]
            self._client = None

    async def resolve_group(self, identifier: str) -> Group:
        await self.connect()
        assert self._client is not None
        entity = await self._client.get_entity(identifier)
        title = (
            getattr(entity, "title", None)
            or getattr(entity, "username", None)
            or str(getattr(entity, "id", identifier))
        )
        return Group(
            telegram_id=int(getattr(entity, "id", 0)),
            title=title,
            username=getattr(entity, "username", None),
        )

    async def stream(self, opts: FetchOptions) -> AsyncIterator[Message]:  # type: ignore[override]
        return self._stream(opts)

    async def _stream(self, opts: FetchOptions) -> AsyncIterator[Message]:
        from telethon.errors import FloodWaitError  # type: ignore

        await self.connect()
        assert self._client is not None

        group = await self.resolve_group(opts.group_identifier)
        log.info("ingest start", extra={"group": group.title, "tg_id": group.telegram_id})

        kwargs: dict[str, object] = {
            "entity": opts.group_identifier,
            "limit": opts.max_messages,
            "reverse": True,  # oldest → newest so incremental sync is trivial
        }
        if opts.offset_date is not None:
            kwargs["offset_date"] = opts.offset_date
        if opts.min_message_id is not None:
            kwargs["min_id"] = opts.min_message_id

        retries = 0
        while True:
            try:
                async for tmsg in self._client.iter_messages(**kwargs):  # type: ignore[attr-defined]
                    if tmsg is None or tmsg.message is None:
                        continue
                    sender_id = (
                        int(tmsg.sender_id)
                        if getattr(tmsg, "sender_id", None) is not None
                        else None
                    )
                    yield Message(
                        telegram_id=int(tmsg.id),
                        group_telegram_id=group.telegram_id,
                        sender_telegram_id=sender_id,
                        text=tmsg.message or "",
                        message_type=_classify(tmsg),
                        sent_at=tmsg.date.replace(tzinfo=None) if tmsg.date else datetime.utcnow(),
                        reply_to=int(tmsg.reply_to_msg_id) if tmsg.reply_to_msg_id else None,
                        raw_meta={"grouped_id": getattr(tmsg, "grouped_id", None)},
                    )
                    await asyncio.sleep(0)  # cooperative yield
                break
            except FloodWaitError as e:
                retries += 1
                wait = float(getattr(e, "seconds", 5))
                log.warning(
                    "flood wait",
                    extra={"seconds": wait, "retries": retries, "group": group.title},
                )
                if retries > 3:
                    raise
                await asyncio.sleep(wait + self._sleep)


def _classify(tmsg) -> str:
    if getattr(tmsg, "forward", None):
        return "forward"
    if getattr(tmsg, "media", None):
        return "media"
    if getattr(tmsg, "reply_to_msg_id", None):
        return "reply"
    if getattr(tmsg, "message", None):
        return "text"
    return "unknown"
