"""Declarative rule engine.

A rule is a list of **conditions** over a message's:
  - `text`              (normalized string)
  - `tokens`            (uppercase tokens)
  - `entities.symbols`  (BTC, ETH, …)
  - `entities.numbers`
  - `entities.urls`
  - `entities.hashtags`
  - `entities.mentions`

Supported condition operators:

    { "contains": "BUY" }                          # substring in normalized text (case-insensitive)
    { "contains_any": ["BUY", "LONG"] }
    { "contains_all": ["BTC", "TARGET"] }
    { "regex": "(?i)\\bSL\\b" }
    { "has_symbol": "BTC" }
    { "has_symbol_any": ["BTC", "ETH"] }
    { "min_numbers": 3 }
    { "has_url": true }

A rule passes only when **every** listed condition passes (AND semantics).
Use `match_type: "any"` at rule-level to flip to OR.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Iterable

from ..logging_setup import get_logger
from ..processing import ExtractedEntities

log = get_logger(__name__)


@dataclass(frozen=True)
class Rule:
    name: str
    conditions: list[dict[str, Any]]
    action: str = "store_signal"
    match_type: str = "all"  # "all" | "any"
    confidence: float = 1.0
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class MatchResult:
    rule: Rule
    matched_conditions: list[str]

    @property
    def passed(self) -> bool:
        return bool(self.matched_conditions)


class RuleEngine:
    """Stateless evaluator. Safe to share across threads / async tasks."""

    def __init__(self, rules: Iterable[Rule]) -> None:
        self._rules: list[Rule] = list(rules)
        log.info("rule engine ready", extra={"rule_count": len(self._rules)})

    @property
    def rules(self) -> list[Rule]:
        return list(self._rules)

    def evaluate(
        self,
        *,
        text: str,
        tokens: list[str],
        entities: ExtractedEntities,
    ) -> list[MatchResult]:
        ctx = _MatchContext(text=text, tokens=tokens, entities=entities)
        out: list[MatchResult] = []
        for rule in self._rules:
            matched = _evaluate_rule(rule, ctx)
            if matched:
                out.append(MatchResult(rule=rule, matched_conditions=matched))
        return out


# ----------------------------------------------------------------------------- internals


@dataclass
class _MatchContext:
    text: str
    tokens: list[str]
    entities: ExtractedEntities


def _evaluate_rule(rule: Rule, ctx: _MatchContext) -> list[str]:
    matched: list[str] = []
    failed: list[str] = []
    for cond in rule.conditions:
        name, ok = _evaluate_condition(cond, ctx)
        (matched if ok else failed).append(name)
    if rule.match_type == "any":
        return matched if matched else []
    # default AND
    return matched if not failed else []


def _evaluate_condition(cond: dict[str, Any], ctx: _MatchContext) -> tuple[str, bool]:
    text_up = ctx.text.upper()

    if "contains" in cond:
        needle = str(cond["contains"]).upper()
        return f"contains:{needle}", needle in text_up

    if "contains_any" in cond:
        needles = [str(n).upper() for n in cond["contains_any"]]
        hit = any(n in text_up for n in needles)
        return f"contains_any:{','.join(needles)}", hit

    if "contains_all" in cond:
        needles = [str(n).upper() for n in cond["contains_all"]]
        hit = all(n in text_up for n in needles)
        return f"contains_all:{','.join(needles)}", hit

    if "regex" in cond:
        pattern = str(cond["regex"])
        try:
            ok = bool(re.search(pattern, ctx.text))
        except re.error as exc:
            log.error("bad regex", extra={"pattern": pattern, "err": str(exc)})
            return f"regex:{pattern}", False
        return f"regex:{pattern}", ok

    if "has_symbol" in cond:
        want = str(cond["has_symbol"]).upper()
        ok = any(want == s or want == s.split("/")[0] for s in ctx.entities.symbols)
        return f"has_symbol:{want}", ok

    if "has_symbol_any" in cond:
        wants = {str(s).upper() for s in cond["has_symbol_any"]}
        ok = any(
            (s in wants) or (s.split("/")[0] in wants) for s in ctx.entities.symbols
        )
        return f"has_symbol_any:{','.join(sorted(wants))}", ok

    if "min_numbers" in cond:
        need = int(cond["min_numbers"])
        ok = len(ctx.entities.numbers) >= need
        return f"min_numbers:{need}", ok

    if "has_url" in cond:
        want = bool(cond["has_url"])
        ok = bool(ctx.entities.urls) == want
        return f"has_url:{want}", ok

    log.warning("unknown condition", extra={"keys": list(cond.keys())})
    return f"unknown:{list(cond.keys())}", False
