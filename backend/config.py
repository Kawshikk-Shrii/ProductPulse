"""
Configuration management for ProductPulse.
Reads API keys, Hindsight endpoints, and model configurations from environment variables.
"""

import os
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict

BASE_DIR = Path(__file__).resolve().parent.parent


class Settings(BaseSettings):
    APP_NAME: str = "ProductPulse"
    APP_VERSION: str = "1.0.0"
    HOST: str = "127.0.0.1"
    PORT: int = 8000

    # Hindsight configuration
    HINDSIGHT_API_URL: str = os.environ.get("HINDSIGHT_API_URL", "http://127.0.0.1:8888")
    HINDSIGHT_API_KEY: str = os.environ.get("HINDSIGHT_API_KEY", "")
    HINDSIGHT_BANK_ID: str = os.environ.get("HINDSIGHT_BANK_ID", "productpulse-ops")

    # LLM Configuration
    GEMINI_API_KEY: str = os.environ.get("GEMINI_API_KEY", "")
    GEMINI_MODEL: str = os.environ.get("GEMINI_MODEL", "gemini-2.5-flash")

    # Storage paths
    DATA_DIR: Path = BASE_DIR / "backend" / "storage"

    model_config = SettingsConfigDict(env_file=".env", extra="allow")


settings = Settings()
settings.DATA_DIR.mkdir(parents=True, exist_ok=True)
