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
from butterfly.infrastructure.sqlite.seeder import write_drivers
from butterfly.infrastructure.memory.story_seed import StorySeed


class SqliteDriverRepo(DriverRepo):
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
