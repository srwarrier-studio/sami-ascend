from dataclasses import dataclass, field

from butterfly.domain.entities.sales_order import SalesOrder


@dataclass(frozen=True)
class ListSalesOrdersQuery:
    filter: str | None = None
    select: str | None = None
    orderby: str | None = None
    top: str | None = None
    skip: str | None = None
    count: str | None = None


@dataclass(frozen=True)
class ListSalesOrdersResult:
    orders: list[SalesOrder]
    total: int | None
    select: list[str] = field(default_factory=list)
