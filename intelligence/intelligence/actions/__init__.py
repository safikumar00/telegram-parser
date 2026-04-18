"""Action system — maps rule.action strings to side-effects."""
from .base import Action, ActionContext, ActionRegistry, default_registry
from .alert import AlertAction
from .forward import ForwardAction
from .store_signal import StoreSignalAction

__all__ = [
    "Action",
    "ActionContext",
    "ActionRegistry",
    "AlertAction",
    "ForwardAction",
    "StoreSignalAction",
    "default_registry",
]
