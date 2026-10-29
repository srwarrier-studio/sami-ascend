from collections.abc import Callable
from datetime import date

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from structured_logging import RequestIdMiddleware
from token_verification import TokenVerifier
from token_verification.fastapi_deps import AuthDependencies

from synapse_api.application.combined_catalog import CombinedCatalog
from synapse_api.application.sales_cache import SalesCache
from synapse_api.application.sales_widgets import SalesWidgetCatalog
from synapse_api.domain.errors import CatalogEntryNotFound, InvalidQuery, SapUnavailable
from synapse_api.domain.gateways.sales_source import SalesSource
from synapse_api.domain.gateways.widget_catalog import WidgetCatalog
from synapse_api.infrastructure.api.catalog.router import create_catalog_router
from synapse_api.infrastructure.api.sales.router import create_sales_router
from synapse_api.infrastructure.mock_library_catalog import MockLibraryCatalog
from synapse_api.infrastructure.settings import Settings


def create_app(
    source: SalesSource,
    settings: Settings,
    today: Callable[[], date] = date.today,
    cache: SalesCache | None = None,
    catalog: WidgetCatalog | None = None,
) -> FastAPI:
    auth = AuthDependencies(TokenVerifier(settings.jwt_secret))
    app = FastAPI()

    @app.exception_handler(InvalidQuery)
    def invalid_query(request: Request, error: InvalidQuery) -> JSONResponse:
        return JSONResponse({"code": "INVALID_QUERY", "message": str(error)}, status_code=422)

    @app.exception_handler(CatalogEntryNotFound)
    def catalog_entry_not_found(request: Request, error: CatalogEntryNotFound) -> JSONResponse:
        return JSONResponse({"code": "CATALOG_ENTRY_NOT_FOUND"}, status_code=404)

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
    widgets = catalog or CombinedCatalog(SalesWidgetCatalog(source, settings.monthly_sales_target), MockLibraryCatalog())
    app.include_router(create_sales_router(source, auth, today, sales_cache), prefix="/v1/synapse", tags=["Sales"])
    app.include_router(create_catalog_router(widgets, auth, today, sales_cache), prefix="/v1/synapse", tags=["Catalog"])
    return app
