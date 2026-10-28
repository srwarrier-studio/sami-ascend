from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[5] / ".env"
DEFAULT_SAP_BASE_URL = "http://localhost:8003/sap/opu/odata4/sap/zui_sales_o4/srvd_a2x/sap/zsales/0001/"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore", frozen=True)
    sap_base_url: str = DEFAULT_SAP_BASE_URL
    sap_timeout_seconds: float = 10.0
    cache_seconds: float = 300
    jwt_secret: str = ""
    frontend_url: str = "http://localhost:5173"
