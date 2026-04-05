"""
Application configuration loaded from environment variables.
"""

from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── Application ──────────────────────────────────
    APP_NAME: str = "RAHATY"
    DEBUG: bool = False
    API_V1_PREFIX: str = "/api/v1"

    # ── Database ─────────────────────────────────────
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/hotel_saas"

    # ── Auth ─────────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440  # 24 hours
    ALGORITHM: str = "HS256"

    # ── OpenAI ───────────────────────────────────────
    OPENAI_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4"

    # ── WhatsApp (Meta Cloud API) ────────────────────
    WHATSAPP_API_URL: str = "https://graph.facebook.com/v21.0"
    WHATSAPP_API_TOKEN: str = ""
    WHATSAPP_VERIFY_TOKEN: str = "your-webhook-verify-token"

    # ── Telegram Bot API ─────────────────────────────
    TELEGRAM_BOT_TOKEN: str = ""

    # ── Email SMTP ───────────────────────────────────
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SENDER_EMAIL: str = ""

    # ── Email IMAP ───────────────────────────────────
    IMAP_HOST: str = "imap.gmail.com"
    IMAP_PORT: int = 993
    IMAP_ENABLED: bool = True

    # ── SLA Policy ──────────────────────────────────
    SLA_FIRST_RESPONSE_MINUTES: int = 15
    SLA_RESOLUTION_HOURS: int = 4

    class Config:
        env_file = ".env"
        case_sensitive = True
        extra = "ignore"


@lru_cache()
def get_settings() -> Settings:
    return Settings()
