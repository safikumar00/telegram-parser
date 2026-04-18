"""Configuration loaded from environment — no hardcoded secrets."""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Load .env next to the project root before Settings is evaluated.
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(_ENV_PATH, override=False)


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
