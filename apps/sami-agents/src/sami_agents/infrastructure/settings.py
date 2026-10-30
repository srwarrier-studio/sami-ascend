from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[5] / ".env"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore", frozen=True)
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "gemma3:270m"
    synapse_url: str = "http://localhost:8004"
    model_timeout_seconds: float = 20.0
    jwt_secret: str = ""
    frontend_url: str = "http://localhost:5173"
