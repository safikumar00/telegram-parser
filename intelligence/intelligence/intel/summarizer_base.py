"""Summarizer contract — removable AI layer.

The rest of the pipeline only ever sees `Summarizer`. The real LLM
implementation lives in `llm_summarizer.py` and is loaded lazily only
when `SUMMARIZER_ENABLED=true`.
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Protocol

from ..storage.models import Message, Summary


class Summarizer(Protocol):
    """Pure contract. No inheritance required — duck-typed."""

    name: str

    async def summarize(
        self, group_telegram_id: int, messages: Iterable[Message]
    ) -> Summary | None: ...


class NullSummarizer:
    """No-op summarizer — used when the AI layer is disabled or misconfigured.

    Returns `None` so the pipeline skips the summary step entirely.
    """

    name = "null"

    async def summarize(
        self, group_telegram_id: int, messages: Iterable[Message]
    ) -> Summary | None:
        _ = (group_telegram_id, list(messages))
        return None


def build_summarizer(
    *,
    enabled: bool,
    provider: str,
    model: str,
    api_key: str | None,
    batch_size: int,
) -> Summarizer:
    """Factory — isolates LLM imports behind a feature flag."""
    if not enabled:
        return NullSummarizer()
    if not api_key:
        return NullSummarizer()
    # Lazy import so uninstalling emergentintegrations is harmless when disabled.
    from .llm_summarizer import LlmSummarizer

    return LlmSummarizer(
        provider=provider,
        model=model,
        api_key=api_key,
        batch_size=batch_size,
    )


def utcnow() -> datetime:
    return datetime.utcnow()
