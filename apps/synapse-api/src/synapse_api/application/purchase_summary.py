from datetime import date, timedelta
from decimal import Decimal

from synapse_api.application.purchase_widgets import CATEGORY_MONTHS, ON_TIME_DAYS, category_totals
from synapse_api.application.sales_summary import headline, money
from synapse_api.application.sales_widgets import month_periods
from synapse_api.domain.gateways.purchase_source import PurchaseSource

PURCHASE_IDS = {"pur-spend", "pur-open", "pur-trend", "pur-vendors", "pur-recent", "pur-ontime", "pur-categories", "pur-by-category-month"}


class GetPurchaseSummary:
    def __init__(self, source: PurchaseSource):
        self.source = source

    def spend(self, period: tuple[date, date], currency: str) -> Decimal:
        return sum((row.net_amount for row in self.source.daily_purchases(*period) if row.currency == currency), Decimal(0))

    def execute(self, today: date, currency: str, show: set[str]) -> list[str]:
        current, previous = month_periods(today)
        now, before = self.spend(current, currency), self.spend(previous, currency)
        sentences = [self.opening(today, current, previous, now, before, currency)]
        if "pur-ontime" in show:
            sentences.append(self.on_time(today, currency))
        if "pur-open" in show:
            sentences.append(self.open_items())
        if "pur-vendors" in show:
            sentences.append(self.biggest_supplier(today, now, currency))
        if "pur-categories" in show:
            sentences.append(self.biggest_category(today, currency))
        return [sentence for sentence in sentences if sentence]

    def opening(self, today: date, current, previous, now: Decimal, before: Decimal, currency: str) -> str | None:
        if now == 0:
            last = today.replace(day=1) - timedelta(days=1)
            total = self.spend((last.replace(day=1), last), currency)
            if total > 0:
                return f"No purchase orders raised yet this month; last month's total was {money(total, currency)}."
        return headline("Purchases", today, current, previous, now, before, currency)

    def on_time(self, today: date, currency: str) -> str | None:
        due = [item for item in self.source.items_due(today - timedelta(days=ON_TIME_DAYS), today) if item.currency == currency]
        if not due:
            return None
        early = sum(1 for item in due if item.actual is not None and item.actual <= item.promised)
        return f"{early / len(due) * 100:.0f}% of purchase items due in the last {ON_TIME_DAYS} days arrived by the promised date ({early} of {len(due)})."

    def open_items(self) -> str | None:
        count = self.source.open_item_count()
        return f"{count} purchase item{'' if count == 1 else 's'} {'is' if count == 1 else 'are'} still open." if count else None

    def biggest_category(self, today: date, currency: str) -> str | None:
        totals = category_totals(self.source, today, currency)
        whole = sum((value for _, value in totals.values()), Decimal(0))
        if whole <= 0:
            return None
        name, value = max(totals.values(), key=lambda item: (item[1], item[0]))
        return f"{name} is the biggest category over the last {CATEGORY_MONTHS} months: {money(value, currency)} ({value / whole * 100:.0f}% of purchases)."

    def biggest_supplier(self, today: date, spend: Decimal, currency: str) -> str | None:
        totals: dict[str, tuple[str, Decimal]] = {}
        for row in self.source.supplier_purchases(today.replace(day=1), today):
            if row.currency == currency:
                name, amount = totals.get(row.supplier, (row.name, Decimal(0)))
                totals[row.supplier] = (name, amount + row.net_amount)
        if not totals or spend <= 0:
            return None
        name, amount = max(totals.values(), key=lambda item: (item[1], item[0]))
        return f"{name} is the biggest supplier this month: {money(amount, currency)} ({amount / spend * 100:.0f}% of purchases)."
