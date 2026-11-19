"""Módulo de configuración y variables de entorno."""

import os
from pathlib import Path
from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")


class Config:
    GEMINI_API_KEY: str = os.getenv("GEMINI_API_KEY", "").strip()
    GEMINI_MODEL: str = os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip()
    BROWSER_PROFILE_DIR: Path = BASE_DIR / os.getenv(
        "BROWSER_PROFILE_DIR", "browser_data"
    )
    HEADLESS: bool = (
        os.getenv("HEADLESS", "false").lower() in ("1", "true", "yes")
    )

    @classmethod
    def validate_api_key(cls) -> bool:
        return bool(cls.GEMINI_API_KEY)

