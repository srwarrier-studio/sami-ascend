import sqlite3

from butterfly.domain.entities.finance import CashPayment
from butterfly.domain.repositories.finance_repo import FinanceRepo
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.mappers import day
from butterfly.infrastructure.sqlite.money import MONEY_SCALE, from_minor
from butterfly.infrastructure.sqlite.seeder import write_cash
from butterfly.infrastructure.sqlite.summaries import summary_table
from butterfly.infrastructure.sqlite.table import SqliteTable

SCALES = {"amount": MONEY_SCALE, "document_amount": MONEY_SCALE}


def payment_from_row(row: sqlite3.Row) -> CashPayment:
    return CashPayment(
        row["payment_document"], day(row["posting_date"]), row["direction"], row["payment_type"], row["partner"], row["partner_name"], row["expense_category"], row["reference"],
        from_minor(row["amount"]), row["currency"], from_minor(row["document_amount"]), row["document_currency"], row["company_code"],
    )


class SqliteFinanceRepo(FinanceRepo):
    def __init__(self, db: Database):
        self.db = db

    @classmethod
    def from_payments(cls, payments: list[CashPayment] | None = None) -> "SqliteFinanceRepo":
        db = Database()
        if payments:
            write_cash(db, payments)
        return cls(db)

    def listing(self, entity: str) -> SqliteTable:
        return SqliteTable(self.db, "cash_payment", lambda rows: [payment_from_row(row) for row in rows], SCALES)

    def summary_listing(self, name: str) -> SqliteTable | None:
        return summary_table(self.db, name)

    def payments(self) -> list[CashPayment]:
        return [payment_from_row(row) for row in self.db.query("SELECT * FROM cash_payment ORDER BY rowid")]
