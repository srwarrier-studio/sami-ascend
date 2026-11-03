from collections.abc import Callable
from datetime import date
from decimal import Decimal
from typing import Annotated

from fastapi import APIRouter, Depends, Query
from token_verification import Role
from token_verification.fastapi_deps import AuthDependencies

from synapse_api.application.sales_cache import SalesCache
from synapse_api.application.board_summary import GetBoardSummary
from synapse_api.domain.errors import InvalidQuery
from synapse_api.domain.gateways.export_source import ExportSource
from synapse_api.domain.gateways.inventory_source import InventorySource
from synapse_api.domain.gateways.production_source import ProductionSource
from synapse_api.domain.gateways.purchase_source import PurchaseSource
from synapse_api.domain.gateways.receivables_source import ReceivablesSource
from synapse_api.domain.gateways.sales_source import SalesSource
from synapse_api.infrastructure.api.scope import company_scope
from synapse_api.infrastructure.api.summary.schemas import SummaryResponse

MAX_WIDGETS = 30


def create_summary_router(
    source: SalesSource,
    target: Decimal,
    auth: AuthDependencies,
    today: Callable[[], date],
    cache: SalesCache,
    default_currency: str = "INR",
    purchases: PurchaseSource | None = None,
    receivables: ReceivablesSource | None = None,
    inventory: InventorySource | None = None,
    production: ProductionSource | None = None,
    exports: ExportSource | None = None,
) -> APIRouter:
    router = APIRouter(dependencies=[Depends(auth.require_roles(Role.MANAGEMENT, Role.ADMIN))])
    Scoped = Annotated[tuple[str, ...], Depends(company_scope(auth))]

    @router.get("/summary")
    def summary(companies: Scoped, widgets: Annotated[str, Query(max_length=1000)] = "", currency: str | None = None) -> SummaryResponse:
        ids = sorted({part for part in widgets.split(",") if part})
        if len(ids) > MAX_WIDGETS:
            raise InvalidQuery(f"at most {MAX_WIDGETS} widgets")
        shown = (currency or default_currency).upper()
        if len(shown) != 3 or not shown.isalpha():
            raise InvalidQuery("currency must be a 3-letter code such as USD or INR")
        return cache.get(
            ("summary", companies, shown, tuple(ids), today()),
            lambda: SummaryResponse(
                currency=shown,
                sentences=GetBoardSummary(
                    source.for_companies(companies),
                    target,
                    purchases.for_companies(companies) if purchases else None,
                    receivables.for_companies(companies) if receivables else None,
                    inventory.for_companies(companies) if inventory else None,
                    production.for_companies(companies) if production else None,
                    exports.for_companies(companies) if exports else None,
                ).execute(today(), shown, set(ids)),
            ),
        )

    return router
