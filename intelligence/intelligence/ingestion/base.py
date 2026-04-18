"""Ingestion contract — any source (Telethon, mock, file-import) implements this."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import AsyncIterator, Optional

from ..storage.models import Group, Message


@dataclass(frozen=True)
class FetchOptions:
    group_identifier: str  # @username, invite link, or numeric id as str
    offset_date: Optional[datetime] = None   # fetch until this date (backwards)
    min_message_id: Optional[int] = None      # incremental sync lower bound
    batch_size: int = 200
    max_messages: Optional[int] = None


class MessageFetcher(ABC):
    """Async iterator over messages.

    `connect()` / `disconnect()` are no-ops for mock but must be honoured by
    real implementations.
    """

    @abstractmethod
    async def connect(self) -> None: ...

    @abstractmethod
    async def disconnect(self) -> None: ...

    @abstractmethod
    async def resolve_group(self, identifier: str) -> Group: ...

    @abstractmethod
    def stream(self, opts: FetchOptions) -> AsyncIterator[Message]: ...
