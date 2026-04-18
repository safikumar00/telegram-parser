"""End-to-end example: fetch → process → rules → store.

Runs in mock mode out of the box. Switch to Telethon by setting
TELEGRAM_API_ID / TELEGRAM_API_HASH / TELEGRAM_PHONE and passing
`--source telethon --group @someGroup`.

Usage:
    python -m scripts.run_pipeline
    python -m scripts.run_pipeline --source mock --group cryptoDesk
    python -m scripts.run_pipeline --source telethon --group @someGroup --since 2026-02-01
"""
from __future__ import annotations

import argparse
import asyncio
import json
import sys
from datetime import datetime
from pathlib import Path

# Make the project root importable when run via `python scripts/run_pipeline.py`.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from intelligence.config import settings  # noqa: E402
from intelligence.ingestion.base import FetchOptions  # noqa: E402
from intelligence.ingestion.mock_fetcher import MockFetcher  # noqa: E402
from intelligence.ingestion.telethon_fetcher import TelethonFetcher  # noqa: E402
from intelligence.logging_setup import configure_logging, get_logger  # noqa: E402
from intelligence.pipeline import build_pipeline  # noqa: E402

log = get_logger(__name__)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Run the intelligence pipeline")
    p.add_argument("--source", choices=["mock", "telethon"], default="mock")
    p.add_argument("--group", default="cryptoDesk", help="@username or numeric id")
    p.add_argument(
        "--since",
        default=None,
        help="ISO date — only fetch messages sent AFTER this date (Telethon only).",
    )
    p.add_argument("--max", type=int, default=None, help="max messages this run")
    p.add_argument("--reset-cursor", action="store_true", help="ignore last_message_id")
    return p.parse_args()


def _build_fetcher(source: str):
    if source == "mock":
        return MockFetcher()
    if not settings.telegram_configured:
        log.error(
            "telethon requires TELEGRAM_API_ID / TELEGRAM_API_HASH / TELEGRAM_PHONE "
            "to be set in .env — falling back to mock"
        )
        return MockFetcher()
    assert settings.telegram_api_id and settings.telegram_api_hash and settings.telegram_phone
    return TelethonFetcher(
        api_id=int(settings.telegram_api_id),
        api_hash=settings.telegram_api_hash,
        phone=settings.telegram_phone,
        session_name=settings.telegram_session_name,
        rate_limit_sleep=settings.fetch_rate_limit_sleep,
    )


async def main() -> int:
    args = parse_args()
    configure_logging(settings.log_level)

    fetcher = _build_fetcher(args.source)
    pipeline = build_pipeline(fetcher=fetcher)

    since: datetime | None = None
    if args.since:
        since = datetime.fromisoformat(args.since)

    opts = FetchOptions(
        group_identifier=args.group,
        offset_date=since,
        min_message_id=0 if args.reset_cursor else None,
        batch_size=settings.fetch_batch_size,
        max_messages=args.max,
    )

    stats = await pipeline.run(opts)
    print(json.dumps({"stats": stats.as_dict()}, indent=2, default=str))
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
