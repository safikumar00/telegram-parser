"""Pattern-detection hooks.

These run AFTER the deterministic rule engine and observe the evaluation
stream. They never gate a signal — they only surface emergent behaviour
(frequency, co-occurrence, drift). Perfect place to plug in lightweight
ML later without touching the deterministic path.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from typing import Any

from ..rules.engine import MatchResult
from ..storage.models import Message


@dataclass
class PatternObservation:
    kind: str
    details: dict[str, Any] = field(default_factory=dict)


class PatternHook(ABC):
    name: str

    @abstractmethod
    def observe(
        self, message: Message, matches: list[MatchResult]
    ) -> list[PatternObservation]: ...

    def flush(self) -> list[PatternObservation]:
        """Emit aggregated observations at batch-end. Default: nothing."""
        return []


class SymbolFrequencyHook(PatternHook):
    """Tracks how often each symbol co-occurs with a rule match."""

    name = "symbol_frequency"

    def __init__(self) -> None:
        self._per_rule: dict[str, Counter] = defaultdict(Counter)

    def observe(self, message: Message, matches: list[MatchResult]) -> list[PatternObservation]:
        for m in matches:
            # Extract symbols by scanning the message text naively — we don't
            # want this hook to require entities to be re-parsed.
            for token in message.text.upper().split():
                cleaned = token.strip(".,!?:;()[]/")
                if cleaned.isalpha() and 2 <= len(cleaned) <= 6:
                    self._per_rule[m.rule.name][cleaned] += 1
        return []

    def flush(self) -> list[PatternObservation]:
        out: list[PatternObservation] = []
        for rule, counter in self._per_rule.items():
            top = counter.most_common(5)
            if top:
                out.append(PatternObservation(kind="symbol_frequency", details={"rule": rule, "top": top}))
        self._per_rule.clear()
        return out


class PatternRegistry:
    def __init__(self, hooks: list[PatternHook] | None = None) -> None:
        self._hooks: list[PatternHook] = list(hooks or [])

    def register(self, hook: PatternHook) -> None:
        self._hooks.append(hook)

    def observe(
        self, message: Message, matches: list[MatchResult]
    ) -> list[PatternObservation]:
        out: list[PatternObservation] = []
        for h in self._hooks:
            out.extend(h.observe(message, matches))
        return out

    def flush(self) -> list[PatternObservation]:
        out: list[PatternObservation] = []
        for h in self._hooks:
            out.extend(h.flush())
        return out


def default_patterns() -> PatternRegistry:
    return PatternRegistry([SymbolFrequencyHook()])
