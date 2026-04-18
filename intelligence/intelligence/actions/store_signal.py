"""Persist a matched rule as a Signal row."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from ..logging_setup import get_logger
from ..storage.models import Signal
from .base import Action, ActionContext

log = get_logger(__name__)


class StoreSignalAction(Action):
    name = "store_signal"

    def execute(self, ctx: ActionContext) -> dict[str, Any]:
        signal = Signal(
            rule_name=ctx.match.rule.name,
            message_id=ctx.message_internal_id,
            group_telegram_id=ctx.message.group_telegram_id,
            matched_conditions=list(ctx.match.matched_conditions),
            confidence=float(ctx.match.rule.confidence),
            created_at=ctx.ts or datetime.utcnow(),
        )
        sid = ctx.repository.insert_signal(ctx.message_internal_id, signal)
        log.info(
            "signal stored",
            extra={
                "signal_id": sid,
                "rule": ctx.match.rule.name,
                "message_internal_id": ctx.message_internal_id,
                "conditions": ctx.match.matched_conditions,
            },
        )
        return {"signal_id": sid, "rule": ctx.match.rule.name}
