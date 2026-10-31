import os
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_ORDER_DB = str(Path(__file__).resolve().parents[3] / "orders.db")
DEFAULT_SAP_BASE_URL = "http://localhost:8003/sap/opu/odata4/sap/zui_sales_o4/srvd_a2x/sap/zsales/0001/"


@dataclass(frozen=True)
class Settings:
    sap_base_url: str = field(default_factory=lambda: os.environ.get("SAP_BASE_URL", DEFAULT_SAP_BASE_URL))
    sap_timeout_seconds: float = 10.0
    jwt_secret: str = field(default_factory=lambda: os.environ.get("JWT_SECRET", ""))
    frontend_url: str = field(default_factory=lambda: os.environ.get("FRONTEND_URL", "http://localhost:5173"))
    sap_write_limit: int = field(default_factory=lambda: int(os.environ.get("SAP_WRITE_LIMIT", "1")))
    sap_write_wait_seconds: float = field(default_factory=lambda: float(os.environ.get("SAP_WRITE_WAIT_SECONDS", "2")))
    order_workers: int = field(default_factory=lambda: int(os.environ.get("ORDER_WORKERS", "1")))
    order_max_attempts: int = field(default_factory=lambda: int(os.environ.get("ORDER_MAX_ATTEMPTS", "8")))
    order_db: str = field(default_factory=lambda: os.environ.get("ORDER_DB", DEFAULT_ORDER_DB))
