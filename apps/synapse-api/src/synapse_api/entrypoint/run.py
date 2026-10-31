import uvicorn

from synapse_api.entrypoint.app import create_app
from synapse_api.infrastructure.butterfly_sales_source import ButterflySalesSource
from synapse_api.infrastructure.odata_reader import ODataReader
from synapse_api.infrastructure.registry_record_source import RegistryRecordSource
from synapse_api.infrastructure.registry_metric_source import RegistryMetricSource
from synapse_api.infrastructure.settings import Settings


def main() -> None:
    settings = Settings()
    if not settings.jwt_secret:
        raise SystemExit("JWT_SECRET is not set")
    readers = {
        "sales": ODataReader(settings.sap_base_url, settings.sap_timeout_seconds),
        "drivers": ODataReader(settings.drivers_base_url, settings.sap_timeout_seconds),
    }
    app = create_app(ButterflySalesSource(settings), settings, metrics=RegistryMetricSource(readers), records=RegistryRecordSource(readers))
    uvicorn.run(app, host="0.0.0.0", port=8004, log_config=None)
