import sqlite3

from butterfly.domain.entities.exports import ExportShipment
from butterfly.domain.repositories.export_repo import ExportRepo
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.mappers import day
from butterfly.infrastructure.sqlite.money import MONEY_SCALE, from_minor
from butterfly.infrastructure.sqlite.seeder import write_exports
from butterfly.infrastructure.sqlite.summaries import summary_table
from butterfly.infrastructure.sqlite.table import SqliteTable

SCALES = {"net_amount": MONEY_SCALE, "document_amount": MONEY_SCALE}


def shipment_from_row(row: sqlite3.Row) -> ExportShipment:
    return ExportShipment(
        row["shipment"], row["sales_order"], row["sold_to_party"], row["customer_name"], row["country"], row["country_name"], row["transport_mode"], day(row["shipment_date"]),
        day(row["expected_arrival_date"]), day(row["actual_arrival_date"]), row["shipment_status"], from_minor(row["net_amount"]), row["currency"], from_minor(row["document_amount"]),
        row["document_currency"], row["company_code"],
    )


class SqliteExportRepo(ExportRepo):
    def __init__(self, db: Database):
        self.db = db

    @classmethod
    def from_shipments(cls, shipments: list[ExportShipment] | None = None) -> "SqliteExportRepo":
        db = Database()
        if shipments:
            write_exports(db, shipments)
        return cls(db)

    def listing(self, entity: str) -> SqliteTable:
        return SqliteTable(self.db, "export_shipment", lambda rows: [shipment_from_row(row) for row in rows], SCALES)

    def summary_listing(self, name: str) -> SqliteTable | None:
        return summary_table(self.db, name)

    def shipments(self) -> list[ExportShipment]:
        return [shipment_from_row(row) for row in self.db.query("SELECT * FROM export_shipment ORDER BY rowid")]
