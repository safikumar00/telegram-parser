"""Text normalization — strips zero-width chars, folds whitespace, optionally
lowercases. Idempotent."""
from __future__ import annotations

import re
import unicodedata

_ZERO_WIDTH = re.compile(r"[\u200b-\u200d\ufeff]")
_WS = re.compile(r"\s+")


def normalize(text: str, *, lowercase: bool = False) -> str:
    if not text:
        return ""
    # Canonical unicode form — avoids accented-lookalike bypass.
    text = unicodedata.normalize("NFKC", text)
    text = _ZERO_WIDTH.sub("", text)
    text = text.replace("\u00a0", " ")
    text = _WS.sub(" ", text).strip()
    return text.lower() if lowercase else text
