from collections.abc import Callable
from datetime import UTC, date, datetime

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from token_verification import Role
from token_verification.fastapi_deps import AuthDependencies

from synapse_api.application.catalog import GetWidgetData, ListCatalog
from synapse_api.application.sales_cache import SalesCache
from synapse_api.domain.errors import InvalidQuery
from synapse_api.domain.gateways.widget_catalog import WidgetCatalog
from synapse_api.infrastructure.api.scope import company_scope
from synapse_api.infrastructure.api.catalog.schemas import CatalogResponse


def create_catalog_router(
    catalog: WidgetCatalog,
    auth: AuthDependencies,
    today: Callable[[], date],
    cache: SalesCache,
    default_currency: str = "USD",
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> APIRouter:
    router = APIRouter(dependencies=[Depends(auth.require_roles(Role.MANAGEMENT, Role.ADMIN))])
    Scoped = Annotated[tuple[str, ...], Depends(company_scope(auth))]

    @router.get("/catalog")
    def list_catalog() -> CatalogResponse:
        return CatalogResponse.from_domain(ListCatalog(catalog).execute())

    @router.get("/catalog/{entry_id}/data")
    def widget_data(companies: Scoped, entry_id: str, currency: str | None = None, top: Annotated[int, Query(ge=1, le=20)] = 5) -> dict:
        shown = (currency or default_currency).upper()
        if len(shown) != 3 or not shown.isalpha():
            raise InvalidQuery("currency must be a 3-letter code such as USD or INR")
        return cache.get(
            ("catalog-data", companies, shown, entry_id, today(), top),
            lambda: {**GetWidgetData(catalog.for_companies(companies)).execute(entry_id, today(), shown, top), "asOf": now().isoformat(timespec="seconds")},
        )

    return router
