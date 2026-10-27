from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[5] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore")
    ENTRA_SECRET: str
    ENTRA_CLIENT_ID: str
    ENTRA_AUTHORITY: str
    ENTRA_REDIRECT_URL: str
    JWT_SECRET: str
    JWT_EXPIRE_MINUTES: int = 30
    SESSION_SECRET: str
    FRONTEND_URL: str = "http://localhost:5173"

settings = Settings()
