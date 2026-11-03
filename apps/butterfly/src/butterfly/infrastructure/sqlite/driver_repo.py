from datetime import date

from butterfly.domain.entities.drivers import (
    CustomerInvoice,
    ProductionOrder,
    ProductionOrderComponent,
    PurchaseDelivery,
    SalesContract,
)
from butterfly.domain.repositories.driver_repo import DriverRepo
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.mappers import (
    component_from_row,
    contract_from_row,
    delivery_from_row,
    invoice_from_row,
    production_order_from_row,
)
from butterfly.infrastructure.sqlite.money import MONEY_SCALE, QUANTITY_SCALE
from butterfly.infrastructure.sqlite.seeder import write_drivers, write_master_data
from butterfly.infrastructure.sqlite.summaries import summary_table
from butterfly.infrastructure.sqlite.table import SqliteTable
from butterfly.infrastructure.memory.story_seed import StorySeed


TABLES = {
    "contracts": ("sales_contract", contract_from_row, {"contract_value": MONEY_SCALE}),
    "deliveries": ("purchase_delivery", delivery_from_row, {"ordered_quantity": QUANTITY_SCALE, "delivered_quantity": QUANTITY_SCALE, "net_amount": MONEY_SCALE}),
    "invoices": ("customer_invoice", invoice_from_row, {"net_amount": MONEY_SCALE, "cleared_amount": MONEY_SCALE}),
    "production_orders": ("production_order", production_order_from_row, {"planned_quantity": QUANTITY_SCALE, "confirmed_quantity": QUANTITY_SCALE}),
    "components": ("production_order_component", component_from_row, {"required_quantity": QUANTITY_SCALE}),
}


class SqliteDriverRepo(DriverRepo):
    def summary_listing(self, name: str, as_of: date | None = None) -> SqliteTable | None:
        return summary_table(self.db, name, as_of)

    def listing(self, entity: str) -> SqliteTable:
        table, mapper, scales = TABLES[entity]
        return SqliteTable(self.db, table, lambda rows: [mapper(row) for row in rows], scales)

    def __init__(self, db: Database):
        self.db = db

    @classmethod
    def from_lists(
        cls,
        contracts: list[SalesContract] | None = None,
        deliveries: list[PurchaseDelivery] | None = None,
        production_orders: list[ProductionOrder] | None = None,
        components: list[ProductionOrderComponent] | None = None,
        invoices: list[CustomerInvoice] | None = None,
    ) -> "SqliteDriverRepo":
        db = Database()
        write_master_data(db)
        write_drivers(db, StorySeed([], contracts or [], deliveries or [], production_orders or [], components or [], invoices or []))
        return cls(db)

    def contracts(self) -> list[SalesContract]:
        return [contract_from_row(row) for row in self.db.query("SELECT * FROM sales_contract ORDER BY rowid")]

    def deliveries(self) -> list[PurchaseDelivery]:
        return [delivery_from_row(row) for row in self.db.query("SELECT * FROM purchase_delivery ORDER BY rowid")]

    def invoices(self) -> list[CustomerInvoice]:
        return [invoice_from_row(row) for row in self.db.query("SELECT * FROM customer_invoice ORDER BY rowid")]

    def production_orders(self) -> list[ProductionOrder]:
        return [production_order_from_row(row) for row in self.db.query("SELECT * FROM production_order ORDER BY rowid")]

    def components(self) -> list[ProductionOrderComponent]:
        return [component_from_row(row) for row in self.db.query("SELECT * FROM production_order_component ORDER BY rowid")]
