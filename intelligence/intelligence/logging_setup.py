"""Structured stdlib-only logging setup.

Every log line is key=value formatted, trivially grep-able, and carries
the module name — easier than pulling in structlog for now.
"""
from __future__ import annotations

import logging
import sys
from typing import Any


class KeyValueFormatter(logging.Formatter):
    _RESERVED = {
        "name",
        "msg",
        "args",
        "levelname",
        "levelno",
        "pathname",
        "filename",
        "module",
        "exc_info",
        "exc_text",
        "stack_info",
        "lineno",
        "funcName",
        "created",
        "msecs",
        "relativeCreated",
        "thread",
        "threadName",
        "processName",
        "process",
        "message",
        "asctime",
        "taskName",
    }

    def format(self, record: logging.LogRecord) -> str:
        extras: dict[str, Any] = {
            k: v for k, v in record.__dict__.items() if k not in self._RESERVED
        }
        base = (
            f"ts={self.formatTime(record, '%Y-%m-%dT%H:%M:%S')} "
            f"level={record.levelname} "
            f"logger={record.name} "
            f"msg={record.getMessage()!r}"
        )
        extra_str = (
            " " + " ".join(f"{k}={v!r}" for k, v in extras.items()) if extras else ""
        )
        if record.exc_info:
            return f"{base}{extra_str}\n{self.formatException(record.exc_info)}"
        return f"{base}{extra_str}"


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger once. Idempotent."""
    root = logging.getLogger()
    if getattr(configure_logging, "_configured", False):
        root.setLevel(level.upper())
        return
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(KeyValueFormatter())
    root.handlers = [handler]
    root.setLevel(level.upper())
    logging.getLogger("telethon").setLevel("WARNING")
    configure_logging._configured = True  # type: ignore[attr-defined]


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)
