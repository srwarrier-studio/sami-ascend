from dataclasses import replace
from datetime import datetime

from butterfly.domain.entities.number_range import PURCHASE_ORDER
from butterfly.domain.entities.purchase_order import PurchaseOrder, PurchaseOrderItem
from butterfly.domain.repositories.purchase_order_repo import PurchaseOrderRepo
from butterfly.infrastructure.memory.in_memory_driver_repo import InMemoryDriverRepo

SEEDED_BY = "SEED"


class InMemoryPurchaseOrderRepo(PurchaseOrderRepo):
    def __init__(self, drivers: InMemoryDriverRepo):
        self.deliveries = drivers.delivery_rows
        self.headers: dict[str, PurchaseOrder] = {}
        self.links: dict[tuple[str, str], tuple[str, str, str]] = {}

    def list_all(self) -> list[PurchaseOrder]:
        numbers = list(dict.fromkeys(d.purchase_order for d in self.deliveries))
        return [order for order in (self.get(number) for number in numbers) if order]

    def get(self, purchase_order: str) -> PurchaseOrder | None:
        rows = [d for d in self.deliveries if d.purchase_order == purchase_order]
        if not rows:
            return None
        items = [PurchaseOrderItem(d, *self.links.get((d.purchase_order, d.purchase_order_item), ("", "", ""))) for d in rows]
        header = self.headers.get(purchase_order)
        if header:
            return replace(header, items=items)
        first = rows[0]
        stamp = datetime.combine(first.order_date, datetime.min.time())
        return PurchaseOrder(
            purchase_order, "NB", first.company_code, "", "", first.supplier, first.transaction_currency, SEEDED_BY, stamp, stamp, items,
        )

    def next_number(self) -> str:
        return PURCHASE_ORDER.next({d.purchase_order for d in self.deliveries})

    def add(self, order: PurchaseOrder) -> None:
        self.headers[order.purchase_order] = replace(order, items=[])
        for item in order.items:
            self.deliveries.append(item.delivery)
            self.links[(order.purchase_order, item.purchase_order_item)] = (item.plant, item.purchase_requisition, item.purchase_requisition_item)

    def cancel_item(self, purchase_order: str, purchase_order_item: str, changed_at: datetime) -> None:
        for index, d in enumerate(self.deliveries):
            if d.purchase_order == purchase_order and d.purchase_order_item == purchase_order_item:
                self.deliveries[index] = replace(d, delivery_status="X")
        header = self.headers.get(purchase_order)
        if header:
            self.headers[purchase_order] = replace(header, last_change_date_time=changed_at)
