"""Smoke tests — run with `python -m pytest /app/intelligence/tests -q`.

Covers the rule engine, entity extractor, and full pipeline via mock fetcher.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import pytest

os.environ.setdefault("SUMMARIZER_ENABLED", "false")
os.environ.setdefault("DATABASE_URL", f"sqlite:///{Path('/tmp/intel-test.db')}")

# Ensure clean DB per test run
_DB = Path("/tmp/intel-test.db")
if _DB.exists():
    _DB.unlink()

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from intelligence.processing import extract_entities, normalize, tokenize
from intelligence.rules.engine import Rule, RuleEngine


def test_normalize_strips_zero_width():
    raw = "BUY\u200b BTC\u200d  62000"
    assert normalize(raw) == "BUY BTC 62000"


def test_tokenize_captures_numbers():
    out = tokenize("BUY BTC 62000 SL 61500")
    assert "BTC" in out and "62000" in out and "SL" in out


def test_extract_entities_basic():
    ent = extract_entities("🔥 BTC/USDT LONG 62000 SL 61500 TP 64000 https://t.me/x")
    assert any(s.startswith("BTC") for s in ent.symbols)
    assert 62000 in ent.numbers
    assert ent.urls and ent.urls[0].startswith("https://")


def test_rule_engine_all():
    engine = RuleEngine([
        Rule(
            name="crypto_signal",
            conditions=[
                {"contains_any": ["BUY", "SELL"]},
                {"has_symbol_any": ["BTC", "ETH"]},
                {"min_numbers": 1},
            ],
        )
    ])
    text = "BUY BTC 62000 SL 61500 TP 64000"
    ent = extract_entities(text)
    matches = engine.evaluate(text=text, tokens=tokenize(text), entities=ent)
    assert len(matches) == 1
    assert matches[0].rule.name == "crypto_signal"


def test_rule_engine_any():
    engine = RuleEngine([
        Rule(
            name="news",
            conditions=[{"contains": "BREAKING"}, {"contains": "ALERT"}],
            match_type="any",
        )
    ])
    text = "BREAKING: SEC approves ETF"
    ent = extract_entities(text)
    matches = engine.evaluate(text=text, tokens=tokenize(text), entities=ent)
    assert len(matches) == 1


@pytest.mark.asyncio
async def test_pipeline_end_to_end(tmp_path, monkeypatch):
    db = tmp_path / "intel.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db}")
    monkeypatch.setenv("SUMMARIZER_ENABLED", "false")
    monkeypatch.setenv("RULES_DIR", "/app/intelligence/rules_config")

    # Re-import settings with the patched env
    import importlib
    import intelligence.config as cfg
    importlib.reload(cfg)
    import intelligence.pipeline as pl
    importlib.reload(pl)

    from intelligence.ingestion.base import FetchOptions
    from intelligence.ingestion.mock_fetcher import MockFetcher

    pipeline = pl.build_pipeline(fetcher=MockFetcher())
    stats = await pipeline.run(FetchOptions(group_identifier="cryptoDesk"))
    assert stats.fetched >= 6
    assert stats.persisted >= 6
    # At least the BUY/SELL signals should match `crypto_signal`
    assert stats.matches >= 2
    assert stats.actions_run >= 2


if __name__ == "__main__":
    # Tiny runner for environments without pytest-asyncio
    asyncio.run(test_pipeline_end_to_end.__wrapped__(Path("/tmp"), _PytestMonkey()))  # type: ignore[attr-defined]
