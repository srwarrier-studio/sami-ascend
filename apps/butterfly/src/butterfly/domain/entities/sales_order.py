from dataclasses import dataclass, field
from datetime import date, datetime, timezone
from decimal import Decimal

from butterfly.domain.entities.master_data import LOCAL_CURRENCY, SALES_ORGANIZATIONS, to_local


@dataclass(frozen=True)
class SalesOrderItem:
    sales_order: str
    sales_order_item: str
    material: str
    material_description: str | None
    quantity: Decimal
    quantity_unit: str
    net_amount: Decimal


@dataclass(frozen=True)
class SalesOrder:
    sales_order: str
    sales_order_type: str
    sold_to_party: str
    customer_name: str | None
    order_date: date
    requested_delivery_date: date | None
    transaction_currency: str
    total_net_amount: Decimal
    overall_status: str
    created_by_user: str
    creation_date_time: datetime
    last_change_date_time: datetime
    items: list[SalesOrderItem] = field(default_factory=list)
    company_code: str = "INA1"
    country: str = "IN"
    sales_organization: str = ""
    distribution_channel: str = "10"
    division: str = "00"
    purchase_order_by_customer: str | None = None

    def __post_init__(self):
        if not self.sales_organization:
            object.__setattr__(self, "sales_organization", SALES_ORGANIZATIONS.get(self.company_code, ""))

    @property
    def total_net_amount_local(self) -> Decimal:
        return to_local(self.total_net_amount, self.transaction_currency)

    @property
    def local_currency(self) -> str:
        return LOCAL_CURRENCY

    @property
    def etag(self) -> str:
        stamp = self.last_change_date_time.astimezone(timezone.utc).strftime("%Y%m%d%H%M%S")
        return f'W/"{stamp}"'
