"""Word/number/punct tokenizer — regex-only. No nltk."""
from __future__ import annotations

import re

_TOKEN = re.compile(r"[A-Za-z][A-Za-z0-9_+/-]*|\d+(?:[.,]\d+)?")


def tokenize(text: str) -> list[str]:
    if not text:
        return []
    return _TOKEN.findall(text)
