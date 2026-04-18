"""Tiny debug tool: connect to Telegram and print all joined dialogs.

Usage:
    python -m scripts.list_groups
    python -m scripts.list_groups --limit 50

Requires TELEGRAM_API_ID / TELEGRAM_API_HASH / TELEGRAM_PHONE in .env.
On first run Telethon will prompt you for the SMS/Telegram login code.
"""
from __future__ import annotations

import argparse
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from intelligence.config import settings, settings_summary  # noqa: E402
from intelligence.logging_setup import configure_logging, get_logger  # noqa: E402

log = get_logger(__name__)


async def main() -> int:
    p = argparse.ArgumentParser(description="List Telegram dialogs you've joined")
    p.add_argument("--limit", type=int, default=200)
    args = p.parse_args()

    configure_logging("INFO")
    log.info("list_groups start", extra=settings_summary())

    if not settings.telegram_configured:
        log.error(
            "Telegram not configured. Set TELEGRAM_API_ID, TELEGRAM_API_HASH, TELEGRAM_PHONE "
            "in /app/intelligence/.env and re-run."
        )
        return 2

    try:
        from telethon import TelegramClient  # type: ignore
    except ImportError:
        log.error("telethon not installed. Run: pip install telethon")
        return 3

    client = TelegramClient(
        settings.telegram_session_name,
        int(settings.telegram_api_id or 0),
        settings.telegram_api_hash or "",
    )

    log.info("connecting…  (first run will prompt for login code)")
    await client.start(phone=settings.telegram_phone)  # type: ignore[func-returns-value]
    log.info("connected")

    print(f"\n{'id':>14}  {'type':<8}  {'username':<28}  title")
    print("-" * 90)

    count = 0
    async for dialog in client.iter_dialogs(limit=args.limit):  # type: ignore[attr-defined]
        entity = dialog.entity
        kind = type(entity).__name__
        username = getattr(entity, "username", None) or ""
        title = dialog.name or ""
        print(f"{entity.id:>14}  {kind:<8}  {'@' + username if username else '':<28}  {title}")
        count += 1

    print("-" * 90)
    print(f"total: {count} dialog(s)")

    await client.disconnect()  # type: ignore[func-returns-value]
    return 0


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
