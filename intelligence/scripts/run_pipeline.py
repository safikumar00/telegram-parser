"""End-to-end example: fetch → process → rules → store.

Runs in mock mode by default so you always see output — even with no Telegram
credentials. Switch to real Telegram with `--source telethon`.

Usage:
    python -m intelligence
    python -m intelligence --source mock --group cryptoDesk
    python -m intelligence --source telethon --group @someGroup --debug
    python -m intelligence --source telethon --group @someGroup --strict
    python -m scripts.run_pipeline --debug
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

from intelligence.config import settings, settings_summary  # noqa: E402
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
    p.add_argument(
        "--debug", action="store_true", help="verbose logs + print loaded env (masked)"
    )
    p.add_argument(
        "--strict",
        action="store_true",
        help="fail fast if Telethon is requested but credentials are missing",
    )
    return p.parse_args()


def _build_fetcher(source: str, strict: bool):
    if source == "mock":
        log.info("fetcher: MockFetcher (deterministic, no network)")
        return MockFetcher()

    if not settings.telegram_configured:
        msg = (
            "source=telethon requires TELEGRAM_API_ID / TELEGRAM_API_HASH / "
            "TELEGRAM_PHONE in .env"
        )
        if strict:
            log.error("fetcher: FAIL-FAST — " + msg)
            raise SystemExit(2)
        log.warning("fetcher: telethon unavailable — falling back to MockFetcher. " + msg)
        log.warning("         use --strict to fail instead of falling back.")
        return MockFetcher()

    assert settings.telegram_api_id and settings.telegram_api_hash and settings.telegram_phone
    log.info(
        "fetcher: TelethonFetcher",
        extra={
            "session": settings.telegram_session_name,
            "phone": settings.telegram_phone,
        },
    )
    return TelethonFetcher(
        api_id=int(settings.telegram_api_id),
        api_hash=settings.telegram_api_hash,
        phone=settings.telegram_phone,
        session_name=settings.telegram_session_name,
        rate_limit_sleep=settings.fetch_rate_limit_sleep,
    )


async def main() -> int:
    args = parse_args()
    configure_logging("DEBUG" if args.debug else settings.log_level)

    log.info("=== intelligence pipeline starting ===")
    log.info("cli args", extra=vars(args))
    log.info("loaded settings", extra=settings_summary())

    fetcher = _build_fetcher(args.source, strict=args.strict)
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
    log.info("=== intelligence pipeline finished ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
