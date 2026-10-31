from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from synapse_api.domain.entities.compare import Comparison, MonthFigure
from synapse_api.domain.entities.kpis import MonthSales, RankedCustomer, RankedMaterial, SalesTotal
from synapse_api.domain.entities.sales import HighValueOrder


class SalesTotalResponse(BaseModel):
    start: date
    end: date
    net_amount: Decimal
    order_count: int
    currency: str


class SalesTotalsResponse(BaseModel):
    totals: list[SalesTotalResponse]

    @classmethod
    def from_domain(cls, totals: list[SalesTotal]) -> "SalesTotalsResponse":
        return cls.model_validate({"totals": totals}, from_attributes=True)


class MonthSalesResponse(BaseModel):
    year: int
    month: int
    net_amount: Decimal
    currency: str


class MonthOnMonthResponse(BaseModel):
    months: list[MonthSalesResponse]

    @classmethod
    def from_domain(cls, months: list[MonthSales]) -> "MonthOnMonthResponse":
        return cls.model_validate({"months": months}, from_attributes=True)


class RankedCustomerResponse(BaseModel):
    customer: str
    name: str
    net_amount: Decimal
    order_count: int
    currency: str


class TopCustomersResponse(BaseModel):
    customers: list[RankedCustomerResponse]

    @classmethod
    def from_domain(cls, customers: list[RankedCustomer]) -> "TopCustomersResponse":
        return cls.model_validate({"customers": customers}, from_attributes=True)


class RankedMaterialResponse(BaseModel):
    material: str
    description: str
    quantity: Decimal
    unit: str
    net_amount: Decimal
    currency: str


class TopMaterialsResponse(BaseModel):
    materials: list[RankedMaterialResponse]

    @classmethod
    def from_domain(cls, materials: list[RankedMaterial]) -> "TopMaterialsResponse":
        return cls.model_validate({"materials": materials}, from_attributes=True)


class HighValueOrderResponse(BaseModel):
    order: str
    customer_name: str
    order_date: date
    net_amount: Decimal
    currency: str
    status: str


class HighValueOrdersResponse(BaseModel):
    orders: list[HighValueOrderResponse]

    @classmethod
    def from_domain(cls, orders: list[HighValueOrder]) -> "HighValueOrdersResponse":
        return cls.model_validate({"orders": orders}, from_attributes=True)


class ChangeRowResponse(BaseModel):
    key: str
    name: str
    current: Decimal
    previous: Decimal
    change: Decimal
    share_of_change_percent: Decimal | None
    unit: str | None = None
    quantity_current: Decimal | None = None
    quantity_previous: Decimal | None = None
    price_current: Decimal | None = None
    price_previous: Decimal | None = None
    volume_effect: Decimal | None = None
    price_effect: Decimal | None = None


class ComparisonResponse(BaseModel):
    currency: str
    current: Decimal
    previous: Decimal
    change: Decimal
    change_percent: Decimal | None
    rows: list[ChangeRowResponse] | None


class CompareResponse(BaseModel):
    comparisons: list[ComparisonResponse]

    @classmethod
    def from_domain(cls, comparisons: list[Comparison]) -> "CompareResponse":
        return cls.model_validate({"comparisons": comparisons}, from_attributes=True)


class TrendMonthResponse(BaseModel):
    year: int
    month: int
    net_amount: Decimal


class MonthFigureResponse(BaseModel):
    currency: str
    net_amount: Decimal
    order_count: int
    previous_change_percent: Decimal | None
    complete: bool
    trend: list[TrendMonthResponse]


class MonthResponse(BaseModel):
    figures: list[MonthFigureResponse]

    @classmethod
    def from_domain(cls, figures: list[MonthFigure]) -> "MonthResponse":
        return cls.model_validate({"figures": figures}, from_attributes=True)
