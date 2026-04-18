"""Rule engine — config-driven deterministic matching."""
from .engine import MatchResult, Rule, RuleEngine
from .loader import load_rules

__all__ = ["MatchResult", "Rule", "RuleEngine", "load_rules"]
