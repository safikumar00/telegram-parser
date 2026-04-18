"""Configuration loaded from environment — no hardcoded secrets."""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Project root = /app/intelligence/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_ENV_PATH = _PROJECT_ROOT / ".env"

# Load .env explicitly BEFORE Settings is built. `override=False` respects any
# variable already set by the shell (so `FOO=x python -m …` still wins).
_ENV_LOADED = load_dotenv(_ENV_PATH, override=False)
if not _ENV_LOADED:
    # Emit via module logger — configure_logging() may not have run yet, but
    # the default stderr handler still catches this.
    logging.getLogger(__name__).warning(
        "dotenv: %s not found or empty — relying on shell environment only",
        _ENV_PATH,
    )


class Settings(BaseSettings):
    """Typed runtime configuration."""

    model_config = SettingsConfigDict(
        env_file=str(_ENV_PATH),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram
    telegram_api_id: Optional[int] = Field(default=None, alias="TELEGRAM_API_ID")
    telegram_api_hash: Optional[str] = Field(default=None, alias="TELEGRAM_API_HASH")
    telegram_phone: Optional[str] = Field(default=None, alias="TELEGRAM_PHONE")
    telegram_session_name: str = Field(default="intelligence", alias="TELEGRAM_SESSION_NAME")

    # Storage
    database_url: str = Field(
        default="sqlite:////app/intelligence/data/intelligence.db",
        alias="DATABASE_URL",
    )

    # Summarizer (removable layer)
    summarizer_enabled: bool = Field(default=True, alias="SUMMARIZER_ENABLED")
    summarizer_provider: str = Field(default="anthropic", alias="SUMMARIZER_PROVIDER")
    summarizer_model: str = Field(
        default="claude-sonnet-4-5-20250929", alias="SUMMARIZER_MODEL"
    )
    summarizer_batch_size: int = Field(default=40, alias="SUMMARIZER_BATCH_SIZE")
    emergent_llm_key: Optional[str] = Field(default=None, alias="EMERGENT_LLM_KEY")

    # Pipeline
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")
    rules_dir: str = Field(
        default="/app/intelligence/rules_config", alias="RULES_DIR"
    )
    fetch_batch_size: int = Field(default=200, alias="FETCH_BATCH_SIZE")
    fetch_rate_limit_sleep: float = Field(default=1.0, alias="FETCH_RATE_LIMIT_SLEEP")

    @field_validator(
        "telegram_api_id", "telegram_api_hash", "telegram_phone", "emergent_llm_key",
        mode="before",
    )
    @classmethod
    def _empty_to_none(cls, v):  # noqa: D401
        """Treat blank .env values as unset."""
        if v is None:
            return None
        if isinstance(v, str) and v.strip() == "":
            return None
        return v

    @property
    def telegram_configured(self) -> bool:
        return bool(
            self.telegram_api_id
            and self.telegram_api_hash
            and self.telegram_phone
        )

    @property
    def sqlite_path(self) -> Path:
        url = self.database_url
        if not url.startswith("sqlite:///"):
            raise ValueError(
                "Only sqlite:/// URLs are handled here. Swap SqliteRepository for Postgres."
            )
        return Path(url.removeprefix("sqlite:///"))


# Singleton settings — import `settings` everywhere.
settings = Settings()


def _mask(value: Optional[str], keep: int = 4) -> str:
    if value is None:
        return "<unset>"
    s = str(value)
    if len(s) <= keep:
        return "***"
    return f"{s[:keep]}…({len(s)} chars)"


def settings_summary() -> dict[str, object]:
    """Return a loggable dict of current settings with secrets masked."""
    return {
        "env_file": str(_ENV_PATH),
        "env_file_loaded": _ENV_LOADED,
        "project_root": str(_PROJECT_ROOT),
        "telegram_configured": settings.telegram_configured,
        "telegram_api_id": settings.telegram_api_id or "<unset>",
        "telegram_api_hash": _mask(settings.telegram_api_hash),
        "telegram_phone": _mask(settings.telegram_phone, keep=4),
        "telegram_session_name": settings.telegram_session_name,
        "database_url": settings.database_url,
        "sqlite_path_exists": settings.sqlite_path.exists() if settings.database_url.startswith("sqlite:///") else "n/a",
        "summarizer_enabled": settings.summarizer_enabled,
        "summarizer_provider": settings.summarizer_provider,
        "summarizer_model": settings.summarizer_model,
        "emergent_llm_key": _mask(settings.emergent_llm_key, keep=10),
        "rules_dir": settings.rules_dir,
        "rules_dir_exists": Path(settings.rules_dir).exists(),
        "log_level": settings.log_level,
    }
