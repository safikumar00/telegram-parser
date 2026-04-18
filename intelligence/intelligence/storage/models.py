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


@dataclass(frozen=True)
class Signal:
    rule_name: str
    message_id: int  # our internal messages.id, set by repo
    group_telegram_id: int
    matched_conditions: list[str]
    confidence: float
    created_at: datetime


@dataclass(frozen=True)
class Summary:
    group_telegram_id: int
    covers_from: datetime
    covers_to: datetime
    message_count: int
    text: str
    model: str
    created_at: datetime
