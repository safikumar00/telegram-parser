"""Historical backfill — fetches messages until a given date.

Usage:
    python -m scripts.fetch_historical --group @cryptoDesk --until 2026-01-01
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from intelligence.config import settings  # noqa: E402
from intelligence.ingestion.base import FetchOptions  # noqa: E402
from intelligence.ingestion.mock_fetcher import MockFetcher  # noqa: E402
from intelligence.ingestion.telethon_fetcher import TelethonFetcher  # noqa: E402
from intelligence.logging_setup import configure_logging, get_logger  # noqa: E402
from intelligence.pipeline import build_pipeline  # noqa: E402

log = get_logger(__name__)


async def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--group", required=True)
    p.add_argument("--until", required=True, help="ISO date (oldest → newest up to this)")
    p.add_argument("--source", choices=["mock", "telethon"], default="telethon")
    p.add_argument("--max", type=int, default=5000)
    args = p.parse_args()

    configure_logging(settings.log_level)

    if args.source == "telethon" and settings.telegram_configured:
        assert settings.telegram_api_id and settings.telegram_api_hash and settings.telegram_phone
        fetcher = TelethonFetcher(
            api_id=int(settings.telegram_api_id),
            api_hash=settings.telegram_api_hash,
            phone=settings.telegram_phone,
            session_name=settings.telegram_session_name,
        )
    else:
        log.warning("using mock fetcher (telethon creds not configured or --source=mock)")
        fetcher = MockFetcher()

    pipeline = build_pipeline(fetcher=fetcher)

    opts = FetchOptions(
        group_identifier=args.group,
        offset_date=datetime.fromisoformat(args.until),
        batch_size=settings.fetch_batch_size,
        max_messages=args.max,
        min_message_id=0,  # full backfill
    )
    stats = await pipeline.run(opts)
    log.info("backfill complete", extra=stats.as_dict())
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
