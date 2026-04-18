"""Load rules from JSON / YAML files in a directory."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import yaml

from ..logging_setup import get_logger
from .engine import Rule

log = get_logger(__name__)


def _coerce(raw: dict) -> Rule:
    return Rule(
        name=str(raw["name"]),
        conditions=list(raw.get("conditions") or []),
        action=str(raw.get("action", "store_signal")),
        match_type=str(raw.get("match_type", "all")),
        confidence=float(raw.get("confidence", 1.0)),
        tags=[str(t) for t in raw.get("tags", [])],
    )


def _parse_file(path: Path) -> Iterable[dict]:
    text = path.read_text()
    if path.suffix.lower() in {".yaml", ".yml"}:
        data = yaml.safe_load(text) or []
    else:
        data = json.loads(text)
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        raise ValueError(f"{path}: rules file must be a list or single object")
    return data


def load_rules(directory: str | Path) -> list[Rule]:
    root = Path(directory)
    if not root.exists():
        log.warning("rules dir missing", extra={"dir": str(root)})
        return []

    rules: list[Rule] = []
    for path in sorted(root.iterdir()):
        if path.is_file() and path.suffix.lower() in {".json", ".yaml", ".yml"}:
            try:
                for raw in _parse_file(path):
                    rules.append(_coerce(raw))
            except Exception as exc:  # noqa: BLE001 — log & continue; bad file shouldn't kill pipeline
                log.error("failed to load rule file", extra={"file": str(path), "err": str(exc)})
    log.info("rules loaded", extra={"count": len(rules), "dir": str(root)})
    return rules
