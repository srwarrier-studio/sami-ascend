from datetime import datetime

from butterfly.domain.entities.number_range import PURCHASE_ORDER
from butterfly.domain.entities.purchase_order import PurchaseOrder, PurchaseOrderItem
from butterfly.domain.repositories.purchase_order_repo import PurchaseOrderRepo
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.mappers import delivery_from_row, moment
from butterfly.infrastructure.sqlite.money import quantity_to_minor, to_minor
from butterfly.infrastructure.sqlite.seeder import iso, marks

SEEDED_BY = "SEED"


class SqlitePurchaseOrderRepo(PurchaseOrderRepo):
    def __init__(self, db: Database):
        self.db = db

    def list_all(self) -> list[PurchaseOrder]:
        numbers = [row["purchase_order"] for row in self.db.query("SELECT purchase_order FROM purchase_delivery GROUP BY purchase_order ORDER BY MIN(rowid)")]
        return [order for order in (self.get(number) for number in numbers) if order]

    def get(self, purchase_order: str) -> PurchaseOrder | None:
        rows = self.db.query(
            "SELECT d.*, COALESCE(l.plant, '') AS plant, COALESCE(l.purchase_requisition, '') AS purchase_requisition, "
            "COALESCE(l.purchase_requisition_item, '') AS purchase_requisition_item FROM purchase_delivery d "
            "LEFT JOIN purchase_order_item_link l ON l.purchase_order = d.purchase_order AND l.purchase_order_item = d.purchase_order_item "
            "WHERE d.purchase_order = ? ORDER BY d.rowid",
            (purchase_order,),
        )
        if not rows:
            return None
        items = [PurchaseOrderItem(delivery_from_row(row), row["plant"], row["purchase_requisition"], row["purchase_requisition_item"]) for row in rows]
        header = self.db.query("SELECT * FROM purchase_order WHERE purchase_order = ?", (purchase_order,))
        if header:
            h = header[0]
            return PurchaseOrder(
                purchase_order, h["order_type"], h["company_code"], h["purchasing_organization"], h["purchasing_group"], h["supplier"],
                h["document_currency"], h["created_by_user"], moment(h["creation_date_time"]), moment(h["last_change_date_time"]), items,
            )
        first = items[0].delivery
        stamp = datetime.combine(first.order_date, datetime.min.time())
        return PurchaseOrder(
            purchase_order, "NB", first.company_code, "", "", first.supplier, first.transaction_currency, SEEDED_BY, stamp, stamp, items,
        )

    def next_number(self) -> str:
        return PURCHASE_ORDER.next(row["purchase_order"] for row in self.db.query("SELECT DISTINCT purchase_order FROM purchase_delivery"))

    def add(self, order: PurchaseOrder) -> None:
        with self.db.transaction():
            self.db.execute(
                f"INSERT INTO purchase_order VALUES ({marks(10)})",
                (order.purchase_order, order.order_type, order.company_code, order.purchasing_organization, order.purchasing_group, order.supplier,
                 order.document_currency, order.created_by_user, iso(order.creation_date_time), iso(order.last_change_date_time)),
            )
            for item in order.items:
                d = item.delivery
                self.db.execute(
                    f"INSERT INTO purchase_delivery VALUES ({marks(18)})",
                    (d.purchase_order, d.purchase_order_item, d.supplier, d.supplier_name, d.material, d.material_description, iso(d.order_date),
                     quantity_to_minor(d.ordered_quantity), quantity_to_minor(d.delivered_quantity), d.quantity_unit, iso(d.promised_delivery_date),
                     iso(d.actual_delivery_date), d.delivery_status, to_minor(d.net_amount), d.transaction_currency, d.company_code,
                     to_minor(d.net_amount_local), d.local_currency),
                )
                self.db.execute(
                    f"INSERT INTO purchase_order_item_link VALUES ({marks(5)})",
                    (d.purchase_order, d.purchase_order_item, item.plant, item.purchase_requisition, item.purchase_requisition_item),
                )

    def cancel_item(self, purchase_order: str, purchase_order_item: str, changed_at: datetime) -> None:
        with self.db.transaction():
            self.db.execute(
                "UPDATE purchase_delivery SET delivery_status = 'X' WHERE purchase_order = ? AND purchase_order_item = ?",
                (purchase_order, purchase_order_item),
            )
            self.db.execute("UPDATE purchase_order SET last_change_date_time = ? WHERE purchase_order = ?", (iso(changed_at), purchase_order))
