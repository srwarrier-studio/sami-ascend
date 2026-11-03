from butterfly.domain.entities.sales_order import SalesOrder
from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.mappers import item_from_row, order_from_row
from butterfly.infrastructure.sqlite.money import quantity_to_minor, to_minor
from butterfly.infrastructure.sqlite.seeder import iso, marks, write_orders

ORDER_UPDATE = (
    "UPDATE sales_order SET sales_order_type = ?, sold_to_party = ?, customer_name = ?, order_date = ?, requested_delivery_date = ?, transaction_currency = ?, "
    "total_net_amount = ?, overall_status = ?, created_by_user = ?, creation_date_time = ?, last_change_date_time = ?, company_code = ?, country = ? WHERE sales_order = ?"
)


class SqliteSalesOrderRepo(SalesOrderRepo):
    def __init__(self, db: Database):
        self.db = db

    @classmethod
    def from_orders(cls, orders: list[SalesOrder]) -> "SqliteSalesOrderRepo":
        db = Database()
        write_orders(db, list({order.sales_order: order for order in orders}.values()))
        return cls(db)

    def list_all(self) -> list[SalesOrder]:
        items: dict[str, list] = {}
        for row in self.db.query("SELECT * FROM sales_order_item ORDER BY rowid"):
            items.setdefault(row["sales_order"], []).append(item_from_row(row))
        return [order_from_row(row, items.get(row["sales_order"], [])) for row in self.db.query("SELECT * FROM sales_order ORDER BY rowid")]

    def get(self, sales_order: str) -> SalesOrder | None:
        rows = self.db.query("SELECT * FROM sales_order WHERE sales_order = ?", (sales_order,))
        if not rows:
            return None
        items = [item_from_row(row) for row in self.db.query("SELECT * FROM sales_order_item WHERE sales_order = ? ORDER BY rowid", (sales_order,))]
        return order_from_row(rows[0], items)

    def next_number(self) -> str:
        latest = self.db.query("SELECT MAX(CAST(sales_order AS INTEGER)) AS latest FROM sales_order")[0]["latest"] or 0
        return f"{latest + 1:010d}"

    def add(self, order: SalesOrder) -> None:
        with self.db.transaction():
            write_orders(self.db, [order], origin="api")

    def update(self, order: SalesOrder) -> None:
        with self.db.transaction():
            self.db.execute(
                ORDER_UPDATE,
                (
                    order.sales_order_type, order.sold_to_party, order.customer_name, iso(order.order_date), iso(order.requested_delivery_date), order.transaction_currency,
                    to_minor(order.total_net_amount), order.overall_status, order.created_by_user, iso(order.creation_date_time), iso(order.last_change_date_time),
                    order.company_code, order.country, order.sales_order,
                ),
            )
            self.db.execute("DELETE FROM sales_order_item WHERE sales_order = ?", (order.sales_order,))
            self.db.insert_many(
                f"INSERT INTO sales_order_item (sales_order, sales_order_item, material, material_description, quantity, quantity_unit, net_amount) VALUES ({marks(7)})",
                [(i.sales_order, i.sales_order_item, i.material, i.material_description, quantity_to_minor(i.quantity), i.quantity_unit, to_minor(i.net_amount)) for i in order.items],
            )
