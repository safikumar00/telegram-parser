"""Intelligence layer: context summarizer + signal extractor + pattern hooks.

Summarizer is behind a Protocol so the main pipeline never imports any LLM
module directly. Flip `SUMMARIZER_ENABLED=false` → pipeline uses `NullSummarizer`
and the emergentintegrations dependency can even be uninstalled.
"""
from .patterns import PatternHook, PatternRegistry, default_patterns
from .signal_extractor import SignalExtractor
from .summarizer_base import NullSummarizer, Summarizer

__all__ = [
    "NullSummarizer",
    "PatternHook",
    "PatternRegistry",
    "SignalExtractor",
    "Summarizer",
    "default_patterns",
]
