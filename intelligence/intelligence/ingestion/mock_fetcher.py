"""Deterministic mock fetcher — zero-network, used for tests + offline dev."""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import AsyncIterator, Optional
from zlib import crc32

from ..storage.models import Group, Message
from .base import FetchOptions, MessageFetcher

_DEFAULT_CORPUS: list[tuple[str, str, Optional[int]]] = [
    ("cryptoDesk", "BUY BTC 62000 SL 61500 TP 64000", 1_001),
    ("cryptoDesk", "ETH/USDT LONG Entry: 3200 Stop Loss 3100 Take Profit 3400", 1_002),
    ("cryptoDesk", "gm fam, watching SOL closely today 👀", 1_003),
    ("cryptoDesk", "SHORT SOL 150 SL 155 TP 140", 1_004),
    ("cryptoDesk", "check this out https://coingecko.com/en/coins/bitcoin", 1_005),
    ("cryptoDesk", "random noise no signal here", 1_006),
    ("newsRoom", "Breaking: SEC approves new ETF, BTC pumps to 65k", 1_007),
    ("newsRoom", "Reuters: CPI print below estimate", 1_008),
]


class MockFetcher(MessageFetcher):
    def __init__(self, corpus: Optional[list[tuple[str, str, Optional[int]]]] = None) -> None:
        self._corpus = corpus or _DEFAULT_CORPUS
        self._group_ids: dict[str, int] = {}

    async def connect(self) -> None:
        return None

    async def disconnect(self) -> None:
        return None

    async def resolve_group(self, identifier: str) -> Group:
        ident = identifier.lstrip("@")
        # Stable synthetic telegram_id — crc32 is process-independent so
        # incremental sync survives across runs.
        tg_id = self._group_ids.setdefault(ident, -1_000_000_000 - crc32(ident.encode()))
        return Group(telegram_id=tg_id, title=f"Mock · {ident}", username=ident)

    async def stream(self, opts: FetchOptions) -> AsyncIterator[Message]:  # type: ignore[override]
        return self._stream(opts)

    async def _stream(self, opts: FetchOptions) -> AsyncIterator[Message]:
        group = await self.resolve_group(opts.group_identifier)
        ident = opts.group_identifier.lstrip("@")
        base = datetime.utcnow() - timedelta(hours=4)
        count = 0
        for idx, (ch, text, mid) in enumerate(self._corpus):
            if ch != ident:
                continue
            message_id = mid if mid is not None else 1_000 + idx
            if opts.min_message_id is not None and message_id <= opts.min_message_id:
                continue
            if opts.offset_date is not None and base + timedelta(minutes=idx) > opts.offset_date:
                continue
            yield Message(
                telegram_id=message_id,
                group_telegram_id=group.telegram_id,
                sender_telegram_id=10_000 + (idx % 3),
                text=text,
                message_type="text",
                sent_at=base + timedelta(minutes=idx),
                reply_to=None,
                raw_meta={"mock": True},
            )
            count += 1
            if opts.max_messages is not None and count >= opts.max_messages:
                return
