from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field

from workspace_api.domain.entities.order_request import OrderRequest
from workspace_api.domain.entities.sales_order import (
    NewSalesOrder,
    NewSalesOrderItem,
    SalesOrder,
    SalesOrderPage,
)


class NewSalesOrderItemBody(BaseModel):
    material: str
    quantity: Decimal
    quantity_unit: str


class NewSalesOrderBody(BaseModel):
    sales_order_type: str
    sold_to_party: str
    transaction_currency: str
    requested_delivery_date: date | None = None
    items: list[NewSalesOrderItemBody]
    company_code: str = Field(max_length=4)

    def to_domain(self) -> NewSalesOrder:
        return NewSalesOrder(
            self.sales_order_type,
            self.sold_to_party,
            self.transaction_currency,
            self.requested_delivery_date,
            [NewSalesOrderItem(i.material, i.quantity, i.quantity_unit) for i in self.items],
            self.company_code,
        )


class SalesOrderItemResponse(BaseModel):
    sales_order_item: str
    material: str
    material_description: str | None
    quantity: Decimal
    quantity_unit: str
    net_amount: Decimal


class SalesOrderResponse(BaseModel):
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
    items: list[SalesOrderItemResponse]
    company_code: str
    country: str

    @classmethod
    def from_domain(cls, order: SalesOrder) -> "SalesOrderResponse":
        return cls.model_validate(order, from_attributes=True)


class SalesOrderPageResponse(BaseModel):
    orders: list[SalesOrderResponse]
    total: int

    @classmethod
    def from_domain(cls, page: SalesOrderPage) -> "SalesOrderPageResponse":
        return cls.model_validate(page, from_attributes=True)


class OrderRequestResponse(BaseModel):
    id: str
    status: str
    attempts: int
    created_at: datetime
    updated_at: datetime
    sales_order: str | None
    details: list[dict] | None
    message: str | None
    order: dict

    @classmethod
    def from_domain(cls, request: OrderRequest) -> "OrderRequestResponse":
        return cls(
            id=request.id, status=request.status, attempts=request.attempts, created_at=request.created_at,
            updated_at=request.updated_at, sales_order=request.sales_order, details=request.details,
            message=request.message, order=request.body,
        )


class OrderRequestsResponse(BaseModel):
    requests: list[OrderRequestResponse]
