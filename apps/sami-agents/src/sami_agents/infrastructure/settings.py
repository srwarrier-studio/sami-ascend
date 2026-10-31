from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[5] / ".env"
GRAPH_FILE = Path(__file__).resolve().parents[3] / "graph.toml"
REGISTRY_FILE = Path(__file__).resolve().parents[5] / "apps/synapse-api/registry.toml"
CONTRACTS_FOLDER = Path(__file__).resolve().parents[5] / "docs/sap"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore", frozen=True)
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = ""
    synapse_url: str = "http://localhost:8004"
    model_timeout_seconds: float = 20.0
    laya_url: str = ""
    laya_api_key: str = ""
    laya_threshold: float = 0.35
    laya_timeout_seconds: float = 5.0
    pass_min_confidence: float = 0.5
    significant_percent: float = 5
    mover_min_percent: float = 10
    mover_min_share: float = 2
    price_majority_percent: float = 50
    sap_is_mock: bool = True
    jwt_secret: str = ""
    frontend_url: str = "http://localhost:5173"
