import sqlite3

from butterfly.domain.entities.production import ProductionConfirmation, WorkCenterDowntime
from butterfly.domain.repositories.production_repo import ProductionRepo
from butterfly.infrastructure.memory.production_seed import ProductionSeed
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.mappers import day
from butterfly.infrastructure.sqlite.money import MONEY_SCALE, QUANTITY_SCALE, from_minor, quantity_from_minor
from butterfly.infrastructure.sqlite.seeder import write_master_data, write_production
from butterfly.infrastructure.sqlite.summaries import summary_table
from butterfly.infrastructure.sqlite.table import SqliteTable

CONFIRMATION_SCALES = {
    "yield_quantity": QUANTITY_SCALE, "scrap_quantity": QUANTITY_SCALE, "target_quantity": QUANTITY_SCALE, "run_hours": MONEY_SCALE,
    "yield_value": MONEY_SCALE, "scrap_value": MONEY_SCALE, "target_value": MONEY_SCALE,
}
DOWNTIME_SCALES = {"downtime_hours": MONEY_SCALE}


def confirmation_from_row(row: sqlite3.Row) -> ProductionConfirmation:
    return ProductionConfirmation(
        row["confirmation_number"], row["confirmation_counter"], row["production_order"], row["material"], row["material_description"], row["plant"], row["work_center"],
        row["work_center_name"], row["shift"], day(row["posting_date"]), quantity_from_minor(row["yield_quantity"]), quantity_from_minor(row["scrap_quantity"]),
        quantity_from_minor(row["target_quantity"]), row["quantity_unit"], row["scrap_reason"], from_minor(row["run_hours"]), from_minor(row["yield_value"]),
        from_minor(row["scrap_value"]), from_minor(row["target_value"]), row["currency"], row["company_code"],
    )


def downtime_from_row(row: sqlite3.Row) -> WorkCenterDowntime:
    return WorkCenterDowntime(
        row["downtime_number"], row["production_order"], row["plant"], row["work_center"], row["work_center_name"], day(row["posting_date"]),
        from_minor(row["downtime_hours"]), row["downtime_cause"], row["company_code"],
    )


class SqliteProductionRepo(ProductionRepo):
    def __init__(self, db: Database):
        self.db = db

    @classmethod
    def from_seed(cls, production: ProductionSeed | None = None) -> "SqliteProductionRepo":
        db = Database()
        write_master_data(db)
        if production is not None:
            write_production(db, production)
        return cls(db)

    def listing(self, entity: str) -> SqliteTable:
        if entity == "confirmations":
            return SqliteTable(self.db, "production_confirmation_row", lambda rows: [confirmation_from_row(row) for row in rows], CONFIRMATION_SCALES, "confirmation_number, confirmation_counter")
        return SqliteTable(self.db, "work_center_downtime_row", lambda rows: [downtime_from_row(row) for row in rows], DOWNTIME_SCALES, "downtime_number")

    def summary_listing(self, name: str) -> SqliteTable | None:
        return summary_table(self.db, name)

    def confirmations(self) -> list[ProductionConfirmation]:
        return [confirmation_from_row(row) for row in self.db.query("SELECT * FROM production_confirmation_row ORDER BY confirmation_number, confirmation_counter")]

    def downtimes(self) -> list[WorkCenterDowntime]:
        return [downtime_from_row(row) for row in self.db.query("SELECT * FROM work_center_downtime_row ORDER BY downtime_number")]
