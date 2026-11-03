from collections.abc import Callable
from datetime import date

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from structured_logging import RequestIdMiddleware
from token_verification import TokenVerifier
from token_verification.fastapi_deps import AuthDependencies

from synapse_api.application.combined_catalog import CombinedCatalog
from synapse_api.application.inventory_widgets import inventory_catalog
from synapse_api.application.production_widgets import production_catalog
from synapse_api.application.purchase_widgets import purchase_catalog
from synapse_api.application.receivables_widgets import receivables_catalog
from synapse_api.application.sales_cache import SalesCache
from synapse_api.application.sales_widgets import SalesWidgetCatalog
from synapse_api.domain.entities.registry import Registry
from synapse_api.domain.errors import CatalogEntryNotFound, CompanyNotAllowed, InvalidQuery, MetricNotFound, RecordTypeNotFound, SapUnavailable
from synapse_api.domain.gateways.inventory_source import InventorySource
from synapse_api.domain.gateways.metric_source import MetricSource
from synapse_api.domain.gateways.production_source import ProductionSource
from synapse_api.domain.gateways.purchase_source import PurchaseSource
from synapse_api.domain.gateways.receivables_source import ReceivablesSource
from synapse_api.domain.gateways.record_source import RecordSource
from synapse_api.domain.gateways.sales_source import SalesSource
from synapse_api.domain.gateways.widget_catalog import WidgetCatalog
from synapse_api.infrastructure.api.catalog.router import create_catalog_router
from synapse_api.infrastructure.api.summary.router import create_summary_router
from synapse_api.infrastructure.api.metrics.router import create_metrics_router
from synapse_api.infrastructure.api.records.router import create_records_router
from synapse_api.infrastructure.api.sales.router import create_sales_router
from synapse_api.infrastructure.mock_library_catalog import MockLibraryCatalog
from synapse_api.infrastructure.registry_loader import load_registry
from synapse_api.infrastructure.settings import Settings


def library_catalog(sales: WidgetCatalog, purchases: PurchaseSource | None, receivables: ReceivablesSource | None, inventory: InventorySource | None = None, production: ProductionSource | None = None) -> CombinedCatalog:
    real = [sales]
    if purchases is not None:
        real.append(purchase_catalog(purchases))
    if receivables is not None:
        real.append(receivables_catalog(receivables))
    if inventory is not None:
        real.append(inventory_catalog(inventory))
    if production is not None:
        real.append(production_catalog(production))
    taken = {entry.id for catalog in real for entry in catalog.entries()}
    return CombinedCatalog(*real, MockLibraryCatalog(without=taken))


def create_app(
    source: SalesSource,
    settings: Settings,
    today: Callable[[], date] = date.today,
    cache: SalesCache | None = None,
    catalog: WidgetCatalog | None = None,
    metrics: MetricSource | None = None,
    records: RecordSource | None = None,
    registry: Registry | None = None,
    purchases: PurchaseSource | None = None,
    receivables: ReceivablesSource | None = None,
    inventory: InventorySource | None = None,
    production: ProductionSource | None = None,
) -> FastAPI:
    auth = AuthDependencies(TokenVerifier(settings.jwt_secret))
    app = FastAPI()

    @app.exception_handler(InvalidQuery)
    def invalid_query(request: Request, error: InvalidQuery) -> JSONResponse:
        return JSONResponse({"code": "INVALID_QUERY", "message": str(error)}, status_code=422)

    @app.exception_handler(CompanyNotAllowed)
    def company_not_allowed(request: Request, error: CompanyNotAllowed) -> JSONResponse:
        return JSONResponse({"code": "COMPANY_NOT_ALLOWED"}, status_code=403)

    @app.exception_handler(CatalogEntryNotFound)
    def catalog_entry_not_found(request: Request, error: CatalogEntryNotFound) -> JSONResponse:
        return JSONResponse({"code": "CATALOG_ENTRY_NOT_FOUND"}, status_code=404)

    @app.exception_handler(MetricNotFound)
    def metric_not_found(request: Request, error: MetricNotFound) -> JSONResponse:
        return JSONResponse({"code": "METRIC_NOT_FOUND"}, status_code=404)

    @app.exception_handler(RecordTypeNotFound)
    def record_type_not_found(request: Request, error: RecordTypeNotFound) -> JSONResponse:
        return JSONResponse({"code": "RECORD_TYPE_NOT_FOUND"}, status_code=404)

    @app.exception_handler(SapUnavailable)
    def unavailable(request: Request, error: SapUnavailable) -> JSONResponse:
        return JSONResponse({"code": "SAP_UNAVAILABLE"}, status_code=503)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    app.add_middleware(RequestIdMiddleware)
    sales_cache = cache or SalesCache(settings.cache_seconds)
    widgets = catalog or library_catalog(SalesWidgetCatalog(source, settings.monthly_sales_target), purchases, receivables, inventory, production)
    app.include_router(create_sales_router(source, auth, today, sales_cache), prefix="/v1/synapse", tags=["Sales"])
    app.include_router(create_catalog_router(widgets, auth, today, sales_cache, settings.default_currency), prefix="/v1/synapse", tags=["Catalog"])
    app.include_router(
        create_summary_router(source, settings.monthly_sales_target, auth, today, sales_cache, settings.default_currency, purchases, receivables, inventory, production), prefix="/v1/synapse", tags=["Summary"]
    )
    known = (registry or load_registry(settings.registry_path)) if metrics is not None or records is not None else None
    if records is not None:
        app.include_router(create_records_router(records, known, auth, today, sales_cache), prefix="/v1/synapse", tags=["Records"])
    if metrics is not None:
        app.include_router(create_metrics_router(metrics, known, auth, today, sales_cache), prefix="/v1/synapse", tags=["Metrics"])
    return app
