"""Domain models used across the pipeline.

Kept as dataclasses (stdlib) so they stay decoupled from the storage layer.
The repository translates these to/from DB rows.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional


@dataclass(frozen=True)
class Group:
    telegram_id: int
    title: str
    username: Optional[str] = None
    last_message_id: int = 0


@dataclass(frozen=True)
class User:
    telegram_id: int
    username: Optional[str] = None
    display_name: Optional[str] = None


@dataclass(frozen=True)
class Message:
    telegram_id: int  # message id within the group (not globally unique)
    group_telegram_id: int
    sender_telegram_id: Optional[int]
    text: str
    message_type: str  # text | media | forward | reply | unknown
    sent_at: datetime
    reply_to: Optional[int] = None
    raw_meta: dict[str, Any] = field(default_factory=dict)


@dataclass
class Signal:
    def __init__(
        self,
        rule_name,
        message_id,
        group_telegram_id,
        matched_conditions,
        confidence,
        created_at,
        metadata_json=None   # ✅ ADD THIS
    ):
        self.rule_name = rule_name
        self.message_id = message_id
        self.group_telegram_id = group_telegram_id
        self.matched_conditions = matched_conditions
        self.confidence = confidence
        self.created_at = created_at
        self.metadata_json = metadata_json   # ✅ ADD THIS


@dataclass(frozen=True)
class Summary:
    group_telegram_id: int
    covers_from: datetime
    covers_to: datetime
    message_count: int
    text: str
    model: str
    created_at: datetime
