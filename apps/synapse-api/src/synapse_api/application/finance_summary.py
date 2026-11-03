from datetime import date
from decimal import Decimal

from synapse_api.application.finance_widgets import CATEGORIES, MIX_DAYS, expense_totals, received
from synapse_api.application.sales_summary import headline, money
from synapse_api.application.sales_widgets import month_periods
from synapse_api.domain.gateways.finance_source import FinanceSource

FINANCE_IDS = {"fin-collections", "fin-collection-target", "fin-cashflow", "fin-payments", "fin-expenses"}
CURRENCY = "INR"


class GetFinanceSummary:
    def __init__(self, source: FinanceSource, target: Decimal):
        self.source = source
        self.target = target

    def execute(self, today: date, currency: str, show: set[str]) -> list[str]:
        sentences = [self.opening(today)]
        if "fin-collection-target" in show:
            sentences.append(self.pace(today))
        if "fin-cashflow" in show:
            sentences.append(self.net(today))
        if "fin-expenses" in show:
            sentences.append(self.largest_cost(today))
        return [sentence for sentence in sentences if sentence]

    def opening(self, today: date) -> str | None:
        current, previous = month_periods(today)
        return headline("Collections", today, current, previous, received(self.source, current), received(self.source, previous), CURRENCY)

    def pace(self, today: date) -> str | None:
        if self.target <= 0:
            return None
        now = received(self.source, month_periods(today)[0])
        return f"Collections are {now / self.target * 100:.0f}% of the {money(self.target, CURRENCY)} monthly target."

    def net(self, today: date) -> str | None:
        rows = self.source.cash_days(*month_periods(today)[0])
        incoming = sum((row.amount for row in rows if row.direction == "I"), Decimal(0))
        outgoing = sum((row.amount for row in rows if row.direction == "O"), Decimal(0))
        if incoming == 0 and outgoing == 0:
            return None
        way = "more in than out" if incoming >= outgoing else "more out than in"
        return f"This month {money(incoming, CURRENCY)} came in and {money(outgoing, CURRENCY)} went out, {money(abs(incoming - outgoing), CURRENCY)} {way}."

    def largest_cost(self, today: date) -> str | None:
        totals = expense_totals(self.source, today)
        whole = sum(totals.values(), Decimal(0))
        if whole <= 0:
            return None
        category, amount = max(totals.items(), key=lambda item: (item[1], item[0]))
        return f"{CATEGORIES.get(category, category.title())} is the largest running cost over the last {MIX_DAYS} days: {money(amount, CURRENCY)} ({amount / whole * 100:.0f}% of costs)."
