import os
from dataclasses import dataclass, field

DEFAULT_SAP_BASE_URL = "http://localhost:8003/sap/opu/odata4/sap/zui_sales_o4/srvd_a2x/sap/zsales/0001/"


@dataclass(frozen=True)
class Settings:
    sap_base_url: str = field(default_factory=lambda: os.environ.get("SAP_BASE_URL", DEFAULT_SAP_BASE_URL))
    sap_timeout_seconds: float = 10.0
    cache_seconds: float = field(default_factory=lambda: float(os.environ.get("CACHE_SECONDS", "300")))
    jwt_secret: str = field(default_factory=lambda: os.environ.get("JWT_SECRET", ""))
    frontend_url: str = field(default_factory=lambda: os.environ.get("FRONTEND_URL", "http://localhost:5173"))
