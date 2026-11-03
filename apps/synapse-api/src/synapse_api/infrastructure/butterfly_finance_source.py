from datetime import date
from decimal import Decimal

from synapse_api.domain.entities.finance import CashDay, ExpenseDay, IncomingPayment
from synapse_api.domain.gateways.finance_source import FinanceSource
from synapse_api.infrastructure.butterfly_purchase_source import day_range
from synapse_api.infrastructure.odata_reader import ODataReader, company_clause


class ButterflyFinanceSource(FinanceSource):
    def __init__(self, reader: ODataReader, companies: tuple[str, ...] | None = None):
        self.reader = reader
        self.companies = companies

    def for_companies(self, companies: tuple[str, ...]) -> "ButterflyFinanceSource":
        return ButterflyFinanceSource(self.reader, companies)

    def company(self) -> str:
        return company_clause("CompanyCode", self.companies)

    def window(self, entity: str, order: str, start: date, end: date) -> list[dict]:
        return self.reader.all_rows(f"{entity}?$filter={day_range('PostingDate', start, end)}{self.company()}&$orderby={order}")

    def cash_days(self, start: date, end: date) -> list[CashDay]:
        rows = self.window("CashSummaryByDay", "PostingDate,Direction,Currency,CompanyCode", start, end)
        return [CashDay(date.fromisoformat(r["PostingDate"]), r["Direction"], r["PaymentCount"], Decimal(r["Amount"])) for r in rows]

    def expense_days(self, start: date, end: date) -> list[ExpenseDay]:
        rows = self.window("ExpenseSummaryByDay", "PostingDate,ExpenseCategory,Currency,CompanyCode", start, end)
        return [ExpenseDay(date.fromisoformat(r["PostingDate"]), r["ExpenseCategory"], r["PaymentCount"], Decimal(r["Amount"])) for r in rows]

    def incoming_payments(self, top: int) -> list[IncomingPayment]:
        path = f"CashPayment?$filter=Direction%20eq%20'I'{self.company()}&$orderby=PostingDate%20desc,PaymentDocument%20desc&$top={top}"
        return [
            IncomingPayment(r["PaymentDocument"], date.fromisoformat(r["PostingDate"]), r["PartnerName"] or r["Partner"] or "", Decimal(r["Amount"]))
            for r in self.reader.get_rows(path)
        ]
