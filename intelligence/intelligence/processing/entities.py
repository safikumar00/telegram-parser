"""Lightweight entity extractor: symbols, numbers, URLs."""
from __future__ import annotations

import re
from dataclasses import dataclass, field

# Broad but bounded — extend by config later if needed.
_KNOWN_SYMBOLS = {
    "BTC", "ETH", "SOL", "BNB", "XRP", "ADA", "DOGE", "AVAX", "DOT",
    "MATIC", "LINK", "LTC", "TRX", "NEAR", "ATOM", "ARB", "OP", "APT",
    "FIL", "ETC", "UNI", "ICP", "HBAR", "XLM", "SUI", "TON", "SHIB",
    "PEPE", "INJ", "RUNE", "SEI", "TIA", "WLD", "FET", "RNDR", "IMX",
}

_RE_SYMBOL = re.compile(r"\b[A-Z]{2,10}(?:/[A-Z]{2,10})?\b")
_RE_NUMBER = re.compile(r"-?\d+(?:[.,]\d+)?")
_RE_URL = re.compile(
    r"https?://[^\s<>\"']+|www\.[^\s<>\"']+", re.IGNORECASE
)
_RE_HASHTAG = re.compile(r"#[A-Za-z0-9_]{2,}")
_RE_MENTION = re.compile(r"@[A-Za-z0-9_]{3,}")


@dataclass(frozen=True)
class ExtractedEntities:
    symbols: list[str] = field(default_factory=list)
    numbers: list[float] = field(default_factory=list)
    urls: list[str] = field(default_factory=list)
    hashtags: list[str] = field(default_factory=list)
    mentions: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, list]:
        return {
            "symbols": list(self.symbols),
            "numbers": list(self.numbers),
            "urls": list(self.urls),
            "hashtags": list(self.hashtags),
            "mentions": list(self.mentions),
        }


def extract_entities(text: str) -> ExtractedEntities:
    if not text:
        return ExtractedEntities()
    upper = text.upper()

    # Symbols: uppercase matches, keep known tickers first.
    raw_syms = _RE_SYMBOL.findall(upper)
    symbols: list[str] = []
    seen: set[str] = set()
    for s in raw_syms:
        # Skip trivial English words captured by the regex.
        if s in {"A", "I", "OK", "TV", "AM", "PM", "USD", "UK", "US", "EU"}:
            continue
        # Prefer bare base ticker if known.
        base = s.split("/")[0]
        if base in _KNOWN_SYMBOLS or s in _KNOWN_SYMBOLS:
            if s not in seen:
                symbols.append(s)
                seen.add(s)

    numbers: list[float] = []
    for m in _RE_NUMBER.findall(text):
        try:
            numbers.append(float(m.replace(",", ".")))
        except ValueError:
            continue

    urls = _RE_URL.findall(text)
    hashtags = [t.lstrip("#") for t in _RE_HASHTAG.findall(text)]
    mentions = [t.lstrip("@") for t in _RE_MENTION.findall(text)]

    return ExtractedEntities(
        symbols=symbols,
        numbers=numbers,
        urls=urls,
        hashtags=hashtags,
        mentions=mentions,
    )
