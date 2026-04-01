from __future__ import annotations
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./dev.db"
    SECRET_KEY: str = "change-me-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60
    TELEGRAM_BOT_TOKEN: Optional[str] = None
    OPENAI_API_KEY: Optional[str] = None
    STRIPE_SECRET_KEY: Optional[str] = None
    STRIPE_PUBLIC_KEY: Optional[str] = None
    STRIPE_WEBHOOK_SECRET: Optional[str] = None
    SMTP_HOST: str = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    # Accept both SMTP_PASSWORD and legacy SMTP_PASS
    SMTP_PASSWORD: Optional[str] = Field(None, validation_alias="SMTP_PASSWORD")
    SMTP_PASS: Optional[str] = Field(None, validation_alias="SMTP_PASS")
    NOTIFY_EMAIL: str = "petropuneiko@gmail.com"
    ADMIN_TOKEN: str = "finadvisor-admin-2026"
    APP_DOMAIN: str = "https://finadvisor.sk"

    class Config:
        env_file = ".env"
        extra = "ignore"
        populate_by_name = True

    @property
    def smtp_pass(self) -> Optional[str]:
        """Return whichever SMTP password env var is set."""
        return self.SMTP_PASSWORD or self.SMTP_PASS


settings = Settings()
