from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[5] / ".env"
UNANSWERED_FILE = Path(__file__).resolve().parents[3] / "unanswered.jsonl"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore", frozen=True)
    jwt_secret: str = ""
    frontend_url: str = "http://localhost:5173"
    laya_url: str = "http://localhost:8000"
    laya_api_key: str = ""
    laya_model: str = "typed-decisions"
    laya_timeout_seconds: float = 5.0
    max_scenarios: int = 4
    scenario_min_probability: float = 0.3
    domain_min_probability: float = 0.4
    unanswered_log: Path = UNANSWERED_FILE
