"""Signal extractor — the deterministic + hookable core of the intelligence layer.

Ownership:
  • Deterministic rule engine  → authoritative.
  • Pattern hooks              → observational, never block signals.
  • Optional AI classifier     → future extension; plug via `set_classifier`.

The extractor is fully usable with zero LLM dependency.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Awaitable, Callable, Optional

from ..logging_setup import get_logger
from ..processing import ExtractedEntities, extract_entities, normalize, tokenize
from ..rules.engine import MatchResult, RuleEngine
from ..storage.models import Message
from .patterns import PatternRegistry

log = get_logger(__name__)

AiClassifier = Callable[[Message, list[MatchResult]], Awaitable[list[MatchResult]]]


@dataclass
class ExtractionOutcome:
    message: Message
    entities: ExtractedEntities
    matches: list[MatchResult]


class SignalExtractor:
    def __init__(
        self,
        rule_engine: RuleEngine,
        patterns: Optional[PatternRegistry] = None,
    ) -> None:
        self._rules = rule_engine
        self._patterns = patterns or PatternRegistry()
        self._classifier: Optional[AiClassifier] = None

    def set_classifier(self, classifier: AiClassifier) -> None:
        """Future-ready hook — a classifier can refine/score matches."""
        self._classifier = classifier

    async def extract(self, message: Message) -> ExtractionOutcome:
        text = normalize(message.text)
        tokens = tokenize(text)
        entities = extract_entities(text)
        matches = self._rules.evaluate(text=text, tokens=tokens, entities=entities)

        if self._classifier is not None:
            try:
                matches = await self._classifier(message, matches)
            except Exception as exc:  # noqa: BLE001
                log.error("ai classifier failed", extra={"err": str(exc)})

        self._patterns.observe(message, matches)

        log.info(
            "extraction",
            extra={
                "tg_msg_id": message.telegram_id,
                "group_tg_id": message.group_telegram_id,
                "symbols": entities.symbols,
                "matches": [m.rule.name for m in matches],
            },
        )
        return ExtractionOutcome(message=message, entities=entities, matches=matches)

    def flush_patterns(self) -> list[Any]:
        obs = self._patterns.flush()
        if obs:
            log.info("pattern observations", extra={"count": len(obs)})
        return obs


def _dummy_ts() -> datetime:  # pragma: no cover - placeholder to keep import graph linear
    return datetime.utcnow()
