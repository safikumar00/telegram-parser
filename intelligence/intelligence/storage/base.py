"""Repository abstraction — swappable backend.

Concrete implementations (SQLite today, Postgres tomorrow) just implement
this Protocol. The rest of the pipeline never imports the concrete class.
"""
from __future__ import annotations

from datetime import datetime
from typing import Iterable, Optional, Protocol

from .models import Group, Message, Signal, Summary, User


class Repository(Protocol):
    # --- lifecycle ---
    def initialize(self) -> None: ...
    def close(self) -> None: ...

    # --- groups / users ---
    def upsert_group(self, group: Group) -> int: ...
    def get_group(self, telegram_id: int) -> Optional[Group]: ...
    def set_last_message_id(self, group_telegram_id: int, message_id: int) -> None: ...
    def upsert_user(self, user: User) -> int: ...

    # --- messages ---
    def insert_messages(self, messages: Iterable[Message]) -> list[int]: ...
    def list_messages(
        self,
        group_telegram_id: Optional[int] = None,
        since: Optional[datetime] = None,
        limit: int = 500,
    ) -> list[tuple[int, Message]]: ...

    # --- signals ---
    def insert_signal(self, message_internal_id: int, signal: Signal) -> Optional[int]: ...
    def list_signals(self, limit: int = 200) -> list[Signal]: ...

    # --- summaries ---
    def insert_summary(self, summary: Summary) -> int: ...
    def list_summaries(self, group_telegram_id: Optional[int] = None, limit: int = 50) -> list[Summary]: ...
