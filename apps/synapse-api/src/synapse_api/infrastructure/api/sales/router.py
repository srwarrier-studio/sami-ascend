from collections.abc import Callable
from datetime import date
from decimal import Decimal

from fastapi import APIRouter, Depends
from token_verification import Role
from token_verification.fastapi_deps import AuthDependencies

from synapse_api.application.month_on_month_sales import GetMonthOnMonthSales
from synapse_api.application.period_sales import GetMonthToDateSales, GetTodaySales, GetYearToDateSales
from synapse_api.application.recent_high_value_orders import GetRecentHighValueOrders
from synapse_api.application.top_sales import GetTopCustomers, GetTopMaterials
from synapse_api.domain.gateways.sales_source import SalesSource
from synapse_api.infrastructure.api.sales.schemas import (
    HighValueOrdersResponse,
    MonthOnMonthResponse,
    SalesTotalsResponse,
    TopCustomersResponse,
    TopMaterialsResponse,
)


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

    @router.get("/sales/month-on-month")
    def month_on_month(months: int = 12) -> MonthOnMonthResponse:
        return MonthOnMonthResponse.from_domain(GetMonthOnMonthSales(source).execute(today(), months))

    @router.get("/sales/top-customers")
    def top_customers(top: int = 5) -> TopCustomersResponse:
        return TopCustomersResponse.from_domain(GetTopCustomers(source).execute(today(), top))

    @router.get("/sales/top-materials")
    def top_materials(top: int = 5) -> TopMaterialsResponse:
        return TopMaterialsResponse.from_domain(GetTopMaterials(source).execute(today(), top))

    @router.get("/sales/high-value-orders")
    def high_value_orders(minimum: Decimal = Decimal(100000), top: int = 5) -> HighValueOrdersResponse:
        return HighValueOrdersResponse.from_domain(GetRecentHighValueOrders(source).execute(minimum, top))

    return router
