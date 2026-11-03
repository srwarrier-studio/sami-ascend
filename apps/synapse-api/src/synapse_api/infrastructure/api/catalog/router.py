from collections.abc import Callable
from datetime import date

from typing import Annotated

from fastapi import APIRouter, Depends, Query
from token_verification.fastapi_deps import AuthDependencies
from token_verification.token_claims import TokenClaims

from synapse_api.application.catalog import GetWidgetData, ListCatalog
from synapse_api.application.sales_cache import SalesCache
from synapse_api.domain.entities.widget_access import WidgetAccess
from synapse_api.domain.errors import CatalogEntryNotFound, InvalidQuery, WidgetNotAllowed
from synapse_api.domain.gateways.widget_catalog import WidgetCatalog
from synapse_api.infrastructure.api.scope import company_scope
from synapse_api.infrastructure.api.catalog.schemas import CatalogResponse


def create_catalog_router(
    catalog: WidgetCatalog,
    auth: AuthDependencies,
    today: Callable[[], date],
    cache: SalesCache,
    access: WidgetAccess,
    default_currency: str = "INR",
) -> APIRouter:
    router = APIRouter()
    claims_of = Depends(auth.require_roles(*access.entry_roles()))
    Scoped = Annotated[tuple[str, ...], Depends(company_scope(auth, *access.entry_roles()))]

    @router.get("/catalog")
    def list_catalog(claims: Annotated[TokenClaims, claims_of]) -> CatalogResponse:
        entries = [entry for entry in ListCatalog(catalog).execute() if access.allows(claims.roles, entry.category)]
        return CatalogResponse.from_domain(entries)

    @router.get("/catalog/{entry_id}/data")
    def widget_data(claims: Annotated[TokenClaims, claims_of], companies: Scoped, entry_id: str, currency: str | None = None, top: Annotated[int, Query(ge=1, le=20)] = 5) -> dict:
        entry = next((candidate for candidate in catalog.entries() if candidate.id == entry_id), None)
        if entry is None:
            raise CatalogEntryNotFound(entry_id)
        if not access.allows(claims.roles, entry.category):
            raise WidgetNotAllowed(entry_id)
        shown = (currency or default_currency).upper()
        if len(shown) != 3 or not shown.isalpha():
            raise InvalidQuery("currency must be a 3-letter code such as USD or INR")
        return cache.get(
            ("catalog-data", companies, shown, entry_id, today(), top),
            lambda: GetWidgetData(catalog.for_companies(companies)).execute(entry_id, today(), shown, top),
        )

    return router
