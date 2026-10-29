from collections.abc import Callable
from datetime import date

from fastapi import APIRouter, Depends
from token_verification import Role
from token_verification.fastapi_deps import AuthDependencies

from synapse_api.application.catalog import GetWidgetData, ListCatalog
from synapse_api.application.sales_cache import SalesCache
from synapse_api.domain.gateways.widget_catalog import WidgetCatalog
from synapse_api.infrastructure.api.catalog.schemas import CatalogResponse


def create_catalog_router(catalog: WidgetCatalog, auth: AuthDependencies, today: Callable[[], date], cache: SalesCache) -> APIRouter:
    router = APIRouter(dependencies=[Depends(auth.require_roles(Role.MANAGEMENT, Role.ADMIN))])

    @router.get("/catalog")
    def list_catalog() -> CatalogResponse:
        return CatalogResponse.from_domain(ListCatalog(catalog).execute())

    @router.get("/catalog/{entry_id}/data")
    def widget_data(entry_id: str) -> dict:
        return cache.get(("catalog-data", entry_id, today()), lambda: GetWidgetData(catalog).execute(entry_id, today()))

    return router
