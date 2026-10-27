from datetime import datetime, timezone
from decimal import Decimal

from workspace_api.domain.entities.sales_order import (
    NewSalesOrder,
    SalesOrder,
    SalesOrderItem,
    SalesOrderPage,
)
from workspace_api.domain.errors import SalesOrderRejected, ValidationDetail
from workspace_api.domain.gateways.sales_order_gateway import SalesOrderGateway


class MockSalesOrderGateway(SalesOrderGateway):
    def __init__(self):
        self.orders: list[SalesOrder] = []
        self.rejection: list[ValidationDetail] | None = None

    def reject_with(self, details: list[ValidationDetail]) -> None:
        self.rejection = details

    def create(self, order: NewSalesOrder) -> SalesOrder:
        if self.rejection:
            raise SalesOrderRejected(self.rejection)
        now = datetime.now(timezone.utc).replace(microsecond=0)
        items = [
            SalesOrderItem(f"{(index + 1) * 10:06d}", i.material, None, i.quantity, i.quantity_unit, Decimal("0.00"))
            for index, i in enumerate(order.items)
        ]
        created = SalesOrder(
            sales_order=f"{len(self.orders) + 1:010d}",
            sales_order_type=order.sales_order_type,
            sold_to_party=order.sold_to_party,
            customer_name=None,
            order_date=now.date(),
            requested_delivery_date=order.requested_delivery_date,
            transaction_currency=order.transaction_currency,
            total_net_amount=Decimal("0.00"),
            overall_status="A",
            created_by_user="MOCK",
            creation_date_time=now,
            last_change_date_time=now,
            items=items,
        )
        self.orders.append(created)
        return created

    def list_recent(self, top: int, skip: int) -> SalesOrderPage:
        newest_first = sorted(self.orders, key=lambda o: o.sales_order, reverse=True)
        return SalesOrderPage(newest_first[skip : skip + top], len(newest_first))
