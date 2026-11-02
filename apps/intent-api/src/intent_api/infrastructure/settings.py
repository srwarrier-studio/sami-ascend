from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[5] / ".env"
UNANSWERED_FILE = Path(__file__).resolve().parents[3] / "unanswered.jsonl"
GRAPH_FILE = Path(__file__).resolve().parents[3] / "graph.toml"
REGISTRY_FILE = Path(__file__).resolve().parents[5] / "apps/synapse-api/registry.toml"
CONTRACTS_FOLDER = Path(__file__).resolve().parents[5] / "docs/sap"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore", frozen=True)
    jwt_secret: str = ""
    frontend_url: str = "http://localhost:5173"
    laya_url: str = "http://localhost:8000"
    laya_api_key: str = ""
    laya_model: str = "typed-decisions"
    laya_timeout_seconds: float = 5.0
    synapse_url: str = "http://localhost:8004"
    synapse_timeout_seconds: float = 10.0
    max_scenarios: int = 4
    significant_percent: float = 5
    mover_min_percent: float = 10
    mover_min_share: float = 2
    price_majority_percent: float = 50
    top_ranked: int = 5
    scenario_min_probability: float = 0.3
    domain_min_probability: float = 0.4
    unanswered_log: Path = UNANSWERED_FILE
