"""LLM-backed summarizer (Claude Sonnet 4.5 via Emergent Universal Key).

Strictly isolated — the rest of the pipeline only knows the `Summarizer`
Protocol. Deleting this file + flipping `SUMMARIZER_ENABLED=false` removes
the AI layer without touching any other module.
"""
from __future__ import annotations

import uuid
from datetime import datetime
from typing import Iterable

from ..logging_setup import get_logger
from ..storage.models import Message, Summary

log = get_logger(__name__)


class LlmSummarizer:
    """Batches messages and asks Claude for a short structured brief.

    The summary is informational: it NEVER feeds back into rule evaluation.
    """

    name = "llm"

    _SYSTEM_PROMPT = (
        "You are a trading-desk analyst. You will receive a batch of raw chat "
        "messages from a single Telegram group. Produce a crisp 4–6 sentence "
        "brief covering: (1) dominant topics, (2) tradable signals mentioned "
        "with pair + direction + levels, (3) notable news or links, (4) overall "
        "sentiment. Be terse, factual, no fluff, no emojis."
    )

    def __init__(
        self,
        *,
        provider: str,
        model: str,
        api_key: str,
        batch_size: int = 40,
    ) -> None:
        self._provider = provider
        self._model = model
        self._api_key = api_key
        self._batch_size = max(1, int(batch_size))

    async def summarize(
        self, group_telegram_id: int, messages: Iterable[Message]
    ) -> Summary | None:
        msgs = list(messages)
        if not msgs:
            return None
        # Cap the batch to keep prompts bounded.
        batch = msgs[-self._batch_size :]
        covers_from = batch[0].sent_at
        covers_to = batch[-1].sent_at

        try:
            from emergentintegrations.llm.chat import LlmChat, UserMessage  # type: ignore
        except Exception as exc:  # noqa: BLE001
            log.warning(
                "emergentintegrations unavailable — summarizer disabled",
                extra={"err": str(exc)},
            )
            return None

        body = "\n".join(
            f"[{m.sent_at.isoformat(timespec='minutes')}] "
            f"u{m.sender_telegram_id or '?'}: {m.text}"
            for m in batch
        )

        try:
            chat = (
                LlmChat(
                    api_key=self._api_key,
                    session_id=f"summarizer-{uuid.uuid4()}",
                    system_message=self._SYSTEM_PROMPT,
                )
                .with_model(self._provider, self._model)
            )
            response = await chat.send_message(
                UserMessage(text=f"Group {group_telegram_id} batch:\n\n{body}")
            )
            text = str(response).strip()
        except Exception as exc:  # noqa: BLE001 — never crash the pipeline on LLM failure
            log.error("summarizer llm call failed", extra={"err": str(exc)})
            return None

        return Summary(
            group_telegram_id=group_telegram_id,
            covers_from=covers_from,
            covers_to=covers_to,
            message_count=len(batch),
            text=text,
            model=f"{self._provider}:{self._model}",
            created_at=datetime.utcnow(),
        )
