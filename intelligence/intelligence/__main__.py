"""Top-level CLI entry point.

Makes `python -m intelligence` work from anywhere. Delegates to the
run_pipeline CLI in scripts/.
"""
from __future__ import annotations

import sys
from pathlib import Path

# Make the sibling `scripts/` folder importable when invoked as `python -m intelligence`.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from scripts.run_pipeline import main  # noqa: E402
import asyncio  # noqa: E402

if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
