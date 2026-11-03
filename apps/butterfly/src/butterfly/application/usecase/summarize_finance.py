from decimal import Decimal

from butterfly.domain.entities.finance import CashSummaryByDay, ExpenseSummaryByDay
from butterfly.domain.repositories.finance_repo import FinanceRepo

ZERO = Decimal("0.00")


class SummarizeFinance:
    def __init__(self, repo: FinanceRepo):
        self.repo = repo

    def cash_by_day(self) -> list[CashSummaryByDay]:
        totals: dict[tuple, list] = {}
        for p in self.repo.payments():
            entry = totals.setdefault((p.posting_date, p.direction, p.currency, p.company_code), [0, ZERO])
            entry[0] += 1
            entry[1] += p.amount
        return [CashSummaryByDay(day, direction, count, amount, currency, company) for (day, direction, currency, company), (count, amount) in sorted(totals.items())]

    def expenses_by_day(self) -> list[ExpenseSummaryByDay]:
        totals: dict[tuple, list] = {}
        for p in self.repo.payments():
            if p.payment_type == "E":
                entry = totals.setdefault((p.posting_date, p.expense_category, p.currency, p.company_code), [0, ZERO])
                entry[0] += 1
                entry[1] += p.amount
        return [ExpenseSummaryByDay(day, category, count, amount, currency, company) for (day, category, currency, company), (count, amount) in sorted(totals.items())]
