import uvicorn

from synapse_api.entrypoint.app import create_app
from synapse_api.infrastructure.butterfly_export_source import ButterflyExportSource
from synapse_api.infrastructure.butterfly_inventory_source import ButterflyInventorySource
from synapse_api.infrastructure.butterfly_production_source import ButterflyProductionSource
from synapse_api.infrastructure.butterfly_purchase_source import ButterflyPurchaseSource
from synapse_api.infrastructure.butterfly_receivables_source import ButterflyReceivablesSource
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
        "inventory": ODataReader(settings.inventory_base_url, settings.sap_timeout_seconds),
        "production": ODataReader(settings.production_base_url, settings.sap_timeout_seconds),
        "export": ODataReader(settings.export_base_url, settings.sap_timeout_seconds),
    }
    app = create_app(
        ButterflySalesSource(settings),
        settings,
        metrics=RegistryMetricSource(readers),
        records=RegistryRecordSource(readers),
        purchases=ButterflyPurchaseSource(readers["drivers"]),
        receivables=ButterflyReceivablesSource(readers["drivers"]),
        inventory=ButterflyInventorySource(readers["inventory"]),
        production=ButterflyProductionSource(readers["production"], readers["drivers"]),
        exports=ButterflyExportSource(readers["export"]),
    )
    uvicorn.run(app, host="0.0.0.0", port=8004, log_config=None)
