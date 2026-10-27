from datetime import datetime, timezone
from decimal import ROUND_HALF_UP, Decimal
from typing import Any, Callable

from butterfly.application.new_order_validator import NewOrder, NewOrderValidator
from butterfly.domain.entities.sales_order import SalesOrder, SalesOrderItem
from butterfly.domain.errors import ValidationFailed
from butterfly.domain.repositories.master_data_repo import MasterDataRepo
from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo

CREATED_BY = "BUTTERFLY"
CENTS = Decimal("0.01")


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class CreateSalesOrder:
    def __init__(
        self,
        repo: SalesOrderRepo,
        master_data: MasterDataRepo,
        now: Callable[[], datetime] = utc_now,
    ):
        self.repo = repo
        self.master_data = master_data
        self.now = now

    def execute(self, body: dict[str, Any]) -> SalesOrder:
        moment = self.now().astimezone(timezone.utc).replace(microsecond=0)
        new_order, details = NewOrderValidator(self.master_data, moment.date()).validate(body)
        if new_order is None:
            raise ValidationFailed(details)
        order = self.build(new_order, self.repo.next_number(), moment)
        self.repo.add(order)
        return order

    def build(self, new_order: NewOrder, number: str, moment: datetime) -> SalesOrder:
        items = [
            SalesOrderItem(
                sales_order=number,
                sales_order_item=f"{(position + 1) * 10:06d}",
                material=item.material.material_id,
                material_description=item.material.description,
                quantity=item.quantity,
                quantity_unit=item.unit,
                net_amount=(item.quantity * item.material.price).quantize(CENTS, ROUND_HALF_UP),
            )
            for position, item in enumerate(new_order.items)
        ]
        return SalesOrder(
            sales_order=number,
            sales_order_type=new_order.sales_order_type,
            sold_to_party=new_order.customer.customer_id,
            customer_name=new_order.customer.name,
            order_date=moment.date(),
            requested_delivery_date=new_order.requested_delivery_date,
            transaction_currency=new_order.currency,
            total_net_amount=sum((item.net_amount for item in items), Decimal("0.00")),
            overall_status="A",
            created_by_user=CREATED_BY,
            creation_date_time=moment,
            last_change_date_time=moment,
            items=items,
        )
