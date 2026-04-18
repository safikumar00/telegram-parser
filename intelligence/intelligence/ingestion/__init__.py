"""Ingestion layer — unified interface over Telethon and a mock source."""
from .base import FetchOptions, MessageFetcher
from .mock_fetcher import MockFetcher
from .telethon_fetcher import TelethonFetcher

__all__ = ["FetchOptions", "MessageFetcher", "MockFetcher", "TelethonFetcher"]
