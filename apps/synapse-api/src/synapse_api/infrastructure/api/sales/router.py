from collections.abc import Callable
from datetime import date

from fastapi import APIRouter, Depends
from token_verification import Role
from token_verification.fastapi_deps import AuthDependencies

from synapse_api.application.period_sales import GetMonthToDateSales, GetTodaySales, GetYearToDateSales
from synapse_api.domain.gateways.sales_source import SalesSource
from synapse_api.infrastructure.api.sales.schemas import SalesTotalsResponse


def create_sales_router(source: SalesSource, auth: AuthDependencies, today: Callable[[], date]) -> APIRouter:
    router = APIRouter(dependencies=[Depends(auth.require_roles(Role.MANAGEMENT, Role.ADMIN))])

    @router.get("/sales/today")
    def sales_today() -> SalesTotalsResponse:
        return SalesTotalsResponse.from_domain(GetTodaySales(source).execute(today()))

    @router.get("/sales/month-to-date")
    def sales_month_to_date() -> SalesTotalsResponse:
        return SalesTotalsResponse.from_domain(GetMonthToDateSales(source).execute(today()))

    @router.get("/sales/year-to-date")
    def sales_year_to_date() -> SalesTotalsResponse:
        return SalesTotalsResponse.from_domain(GetYearToDateSales(source).execute(today()))

    return router
