from datetime import date
from decimal import Decimal

from synapse_api.application.sales_summary import money
from synapse_api.domain.gateways.receivables_source import ReceivablesSource

RECEIVABLES_IDS = {"fin-receivables", "fin-ageing", "fin-overdue"}
LATE_BUCKETS = {"31-60", "61-90", "90+"}


class GetReceivablesSummary:
    def __init__(self, source: ReceivablesSource):
        self.source = source

    def execute(self, today: date, currency: str, show: set[str]) -> list[str]:
        sentences = [self.opening(today, currency)]
        if "fin-overdue" in show:
            sentences.append(self.most_overdue(today, currency))
        if "fin-ageing" in show:
            sentences.append(self.late(today, currency))
        return [sentence for sentence in sentences if sentence]

    def opening(self, today: date, currency: str) -> str | None:
        rows = [row for row in self.source.totals(today) if row.currency == currency]
        open_amount = sum((row.open_amount for row in rows), Decimal(0))
        if open_amount <= 0:
            return None
        overdue = sum((row.overdue_amount for row in rows), Decimal(0))
        return f"{money(open_amount, currency)} is outstanding from customers, {money(overdue, currency)} ({overdue / open_amount * 100:.0f}%) of it past its due date."

    def most_overdue(self, today: date, currency: str) -> str | None:
        totals: dict[str, tuple[str, Decimal]] = {}
        for row in self.source.by_customer(today):
            if row.currency == currency and row.overdue_amount > 0:
                name, amount = totals.get(row.customer, (row.name, Decimal(0)))
                totals[row.customer] = (name, amount + row.overdue_amount)
        if not totals:
            return None
        name, amount = max(totals.values(), key=lambda item: (item[1], item[0]))
        return f"{name} has the most overdue: {money(amount, currency)}."

    def late(self, today: date, currency: str) -> str | None:
        amount = sum((row.open_amount for row in self.source.ageing(today) if row.currency == currency and row.bucket in LATE_BUCKETS), Decimal(0))
        return f"{money(amount, currency)} is more than 30 days past due." if amount > 0 else None
