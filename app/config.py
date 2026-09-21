"""App configuration loaded from .env."""

from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    """Application settings loaded from environment variables and `.env`."""

    siapkerja_username: str = ""
    siapkerja_password: str = ""
    hari_libur: str = "Sabtu,Minggu"
    latitude: str = "-6.2088"
    longitude: str = "106.8456"
    location: str = "Jakarta"
    activity_log: str = ""
    lesson_learned: str = ""
    obstacles: str = ""
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    api_base: str = "https://monev-api.maganghub.kemnaker.go.id/api/v1"
    auth_base: str = "https://account.kemnaker.go.id"

    model_config = {
        "env_file": Path(__file__).parent.parent / ".env",
        "env_file_encoding": "utf-8",
        "extra": "ignore",
    }


settings = Settings()
