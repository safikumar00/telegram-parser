"""Action registry — rules.action → callable side-effect."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Any

from ..rules.engine import MatchResult
from ..storage.base import Repository
from ..storage.models import Message


@dataclass(frozen=True)
class ActionContext:
    message_internal_id: int
    message: Message
    match: MatchResult
    repository: Repository
    ts: datetime


class Action(ABC):
    name: str

    @abstractmethod
    def execute(self, ctx: ActionContext) -> dict[str, Any]:
        """Run the side-effect. Must not raise on expected conditions."""


class ActionRegistry:
    def __init__(self) -> None:
        self._by_name: dict[str, Action] = {}

    def register(self, action: Action) -> None:
        self._by_name[action.name] = action

    def get(self, name: str) -> Action | None:
        return self._by_name.get(name)

    def names(self) -> list[str]:
        return list(self._by_name.keys())


default_registry = ActionRegistry()
