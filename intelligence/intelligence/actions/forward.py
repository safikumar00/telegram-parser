"""Forward action — stub for future relaying to other channels."""
from __future__ import annotations

from typing import Any

from ..logging_setup import get_logger
from .base import Action, ActionContext

log = get_logger(__name__)


class ForwardAction(Action):
    name = "forward"

    def execute(self, ctx: ActionContext) -> dict[str, Any]:
        log.info(
            "forward (stub)",
            extra={
                "rule": ctx.match.rule.name,
                "group_tg_id": ctx.message.group_telegram_id,
                "message_tg_id": ctx.message.telegram_id,
            },
        )
        return {"forwarded": False, "reason": "forwarder not configured"}
