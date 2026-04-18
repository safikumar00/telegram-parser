"""Alert action — stub for future webhook / push integration."""
from __future__ import annotations

from typing import Any

from ..logging_setup import get_logger
from .base import Action, ActionContext

log = get_logger(__name__)


class AlertAction(Action):
    """Logs as WARNING so ops can tail for alerts.
    Replace `execute` body with webhook / pager integration when available.
    """

    name = "alert"

    def execute(self, ctx: ActionContext) -> dict[str, Any]:
        log.warning(
            "ALERT",
            extra={
                "rule": ctx.match.rule.name,
                "group_tg_id": ctx.message.group_telegram_id,
                "message_tg_id": ctx.message.telegram_id,
                "text": ctx.message.text[:280],
            },
        )
        return {"alerted": True, "rule": ctx.match.rule.name}
