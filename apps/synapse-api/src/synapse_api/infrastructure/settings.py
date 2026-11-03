from decimal import Decimal
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

ENV_FILE = Path(__file__).resolve().parents[5] / ".env"
REGISTRY_PATH = Path(__file__).resolve().parents[3] / "registry.toml"
DEFAULT_DRIVERS_BASE_URL = "http://localhost:8003/sap/opu/odata4/sap/zui_drivers_o4/srvd_a2x/sap/zdrivers/0001/"
DEFAULT_INVENTORY_BASE_URL = "http://localhost:8003/sap/opu/odata4/sap/zui_inventory_o4/srvd_a2x/sap/zinventory/0001/"
DEFAULT_SAP_BASE_URL = "http://localhost:8003/sap/opu/odata4/sap/zui_sales_o4/srvd_a2x/sap/zsales/0001/"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=ENV_FILE, extra="ignore", frozen=True)
    sap_base_url: str = DEFAULT_SAP_BASE_URL
    drivers_base_url: str = DEFAULT_DRIVERS_BASE_URL
    inventory_base_url: str = DEFAULT_INVENTORY_BASE_URL
    registry_path: Path = REGISTRY_PATH
    sap_timeout_seconds: float = 10.0
    cache_seconds: float = 300
    monthly_sales_target: Decimal = Decimal(5000000)
    default_currency: str = "INR"
    jwt_secret: str = ""
    frontend_url: str = "http://localhost:5173"
