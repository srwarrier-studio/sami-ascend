import sqlite3

from butterfly.domain.entities.inventory import MaterialStock, StockMovement, StockValueMonth
from butterfly.domain.repositories.inventory_repo import InventoryRepo
from butterfly.infrastructure.memory.inventory_seed import InventorySeed
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.mappers import day, moment
from butterfly.infrastructure.sqlite.money import MONEY_SCALE, QUANTITY_SCALE, from_minor, quantity_from_minor
from butterfly.infrastructure.sqlite.seeder import write_inventory, write_master_data
from butterfly.infrastructure.sqlite.summaries import summary_table
from butterfly.infrastructure.sqlite.table import SqliteTable

STOCK_SCALES = {"stock_quantity": QUANTITY_SCALE, "stock_value": MONEY_SCALE, "reorder_level": QUANTITY_SCALE}
MOVEMENT_SCALES = {"quantity": QUANTITY_SCALE, "amount": MONEY_SCALE}
STOCK_ORDER = "material, plant, storage_location"


def stock_from_row(row: sqlite3.Row) -> MaterialStock:
    return MaterialStock(
        row["material"], row["material_description"], row["material_group"], row["material_group_name"], row["plant"], row["storage_location"], row["storage_location_name"],
        quantity_from_minor(row["stock_quantity"]), row["quantity_unit"], from_minor(row["stock_value"]), row["currency"], quantity_from_minor(row["reorder_level"]),
        day(row["last_movement_date"]), row["company_code"],
    )


def movement_from_row(row: sqlite3.Row) -> StockMovement:
    return StockMovement(
        row["material_document"], row["material_document_item"], row["material_document_year"], day(row["posting_date"]), moment(row["entry_date_time"]), row["material"],
        row["material_description"], row["plant"], row["storage_location"], row["movement_type"], row["debit_credit_code"], quantity_from_minor(row["quantity"]),
        row["quantity_unit"], from_minor(row["amount"]), row["currency"], row["company_code"],
    )


class SqliteInventoryRepo(InventoryRepo):
    def __init__(self, db: Database):
        self.db = db

    @classmethod
    def from_seed(cls, inventory: InventorySeed | None = None) -> "SqliteInventoryRepo":
        db = Database()
        write_master_data(db)
        if inventory is not None:
            write_inventory(db, inventory)
        return cls(db)

    def listing(self, entity: str) -> SqliteTable:
        if entity == "stocks":
            return SqliteTable(self.db, "material_stock_row", lambda rows: [stock_from_row(row) for row in rows], STOCK_SCALES, STOCK_ORDER)
        return SqliteTable(self.db, "stock_movement", lambda rows: [movement_from_row(row) for row in rows], MOVEMENT_SCALES)

    def summary_listing(self, name: str) -> SqliteTable | None:
        return summary_table(self.db, name)

    def stocks(self) -> list[MaterialStock]:
        return [stock_from_row(row) for row in self.db.query(f"SELECT * FROM material_stock_row ORDER BY {STOCK_ORDER}")]

    def movements(self) -> list[StockMovement]:
        return [movement_from_row(row) for row in self.db.query("SELECT * FROM stock_movement ORDER BY rowid")]

    def monthly_values(self) -> list[StockValueMonth]:
        rows = self.db.query("SELECT * FROM stock_value_month ORDER BY company_code, posting_period")
        return [StockValueMonth(row["posting_period"], from_minor(row["stock_value"]), row["currency"], row["company_code"]) for row in rows]
