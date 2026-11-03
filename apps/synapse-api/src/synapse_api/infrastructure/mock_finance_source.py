from datetime import date

from synapse_api.domain.entities.finance import CashDay, ExpenseDay, IncomingPayment
from synapse_api.domain.gateways.finance_source import FinanceSource


class MockFinanceSource(FinanceSource):
    def __init__(self, cash: list[CashDay] | None = None, expenses: list[ExpenseDay] | None = None, payments: list[IncomingPayment] | None = None):
        self.cash = cash or []
        self.expenses = expenses or []
        self.payments = payments or []

    def for_companies(self, companies: tuple[str, ...]) -> "MockFinanceSource":
        return self

    def cash_days(self, start: date, end: date) -> list[CashDay]:
        return [row for row in self.cash if start <= row.day <= end]

    def expense_days(self, start: date, end: date) -> list[ExpenseDay]:
        return [row for row in self.expenses if start <= row.day <= end]

    def incoming_payments(self, top: int) -> list[IncomingPayment]:
        return sorted(self.payments, key=lambda p: (p.day, p.payment), reverse=True)[:top]
