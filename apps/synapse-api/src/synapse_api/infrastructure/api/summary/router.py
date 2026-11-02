from collections.abc import Callable
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends
from token_verification import Role
from token_verification.fastapi_deps import AuthDependencies

from synapse_api.application.sales_cache import SalesCache
from synapse_api.application.sales_summary import GetSalesSummary
from synapse_api.domain.errors import InvalidQuery
from synapse_api.domain.gateways.sales_source import SalesSource
from synapse_api.infrastructure.api.scope import company_scope
from synapse_api.infrastructure.api.summary.schemas import SummaryResponse


def create_summary_router(
    source: SalesSource,
    target: Decimal,
    auth: AuthDependencies,
    today: Callable[[], date],
    cache: SalesCache,
    default_currency: str = "USD",
    now: Callable[[], datetime] = lambda: datetime.now(UTC),
) -> APIRouter:
    router = APIRouter(dependencies=[Depends(auth.require_roles(Role.MANAGEMENT, Role.ADMIN))])
    Scoped = Annotated[tuple[str, ...], Depends(company_scope(auth))]

    @router.get("/summary")
    def summary(companies: Scoped, currency: str | None = None) -> SummaryResponse:
        shown = (currency or default_currency).upper()
        if len(shown) != 3 or not shown.isalpha():
            raise InvalidQuery("currency must be a 3-letter code such as USD or INR")
        return cache.get(
            ("summary", companies, shown, today()),
            lambda: SummaryResponse(
                asOf=now().isoformat(timespec="seconds"),
                currency=shown,
                sentences=GetSalesSummary(source.for_companies(companies), target).execute(today(), shown),
            ),
        )

    return router
