from datetime import date, timedelta
from decimal import Decimal

from synapse_api.application.export_widgets import TREND_MONTHS, months_start
from synapse_api.application.sales_widgets import MONTH_NAMES, TOP, Period, SalesKpiWidget, day_label, month_note, month_periods
from synapse_api.application.source_catalog import SourceCatalog
from synapse_api.domain.entities.catalog import CatalogEntry
from synapse_api.domain.gateways.finance_source import FinanceSource

MIX_DAYS = 90
CATEGORIES = {"SALARIES": "Salaries", "RENT": "Rent", "UTILITIES": "Utilities", "FREIGHT": "Freight", "MAINTENANCE": "Maintenance", "MARKETING": "Marketing"}


def received(source: FinanceSource, period: Period) -> Decimal:
    return sum((row.amount for row in source.cash_days(*period) if row.direction == "I"), Decimal(0))


def monthly(source: FinanceSource, today: date, direction: str) -> list[tuple[int, Decimal]]:
    first = months_start(today, TREND_MONTHS - 1)
    sums: dict[tuple[int, int], Decimal] = {}
    for row in source.cash_days(first, today):
        if row.direction == direction:
            key = (row.day.year, row.day.month)
            sums[key] = sums.get(key, Decimal(0)) + row.amount
    base = first.year * 12 + first.month - 1
    return [(base + n, sums.get(((base + n) // 12, (base + n) % 12 + 1), Decimal(0))) for n in range(TREND_MONTHS)]


def expense_totals(source: FinanceSource, today: date) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for row in source.expense_days(today - timedelta(days=MIX_DAYS - 1), today):
        totals[row.category] = totals.get(row.category, Decimal(0)) + row.amount
    return totals


class CollectionsWidget(SalesKpiWidget):
    measure = "collections"

    def amount(self, period: Period, currency: str) -> Decimal:
        return received(self.source, period)


class CollectionTargetWidget:
    def __init__(self, source: FinanceSource, entry: CatalogEntry, target: Decimal):
        self.source = source
        self.entry = entry
        self.target = target

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        now = received(self.source, month_periods(today)[0])
        return {"title": self.entry.title, "measure": "collections", "value": float(now), "target": float(self.target), "valueFormat": "currency", "caption": "this month"}


class CashflowWidget:
    def __init__(self, source: FinanceSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        def points(direction: str) -> list[dict]:
            return [{"label": MONTH_NAMES[index % 12], "value": float(amount)} for index, amount in monthly(self.source, today, direction)]

        return {"title": self.entry.title, "measure": "cash", "valueFormat": "currency", "data": points("I"), "compare": points("O"), "label": "Cash in", "compareLabel": "Cash out"}


class PaymentsWidget:
    def __init__(self, source: FinanceSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        return {
            "title": self.entry.title,
            "columns": [
                {"key": "payment", "label": "Payment"},
                {"key": "customer", "label": "Customer"},
                {"key": "date", "label": "Received"},
                {"key": "amount", "label": "Amount", "format": "currency"},
            ],
            "rows": [{"payment": p.payment, "customer": p.customer, "date": day_label(p.day), "amount": float(p.amount)} for p in self.source.incoming_payments(top)],
        }


class ExpensesWidget:
    def __init__(self, source: FinanceSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        ranked = sorted(expense_totals(self.source, today).items(), key=lambda item: (-item[1], item[0]))
        return {"title": self.entry.title, "measure": "expenses", "valueFormat": "currency", "slices": [{"label": CATEGORIES.get(c, c.title()), "value": float(a)} for c, a in ranked if a > 0]}


def build_finance_widgets(source: FinanceSource, collection_target: Decimal) -> list:
    def entry(id: str, title: str, description: str, widget: str) -> CatalogEntry:
        return CatalogEntry(id, title, description, "Finance", widget)

    def trend(today: date, currency: str) -> list[float]:
        return [float(amount) for _, amount in monthly(source, today, "I")]

    return [
        CollectionsWidget(source, entry("fin-collections", "Collections this month", "Payments received so far this month against the same days last month.", "KpiCard"), month_periods, trend, month_note),
        CollectionTargetWidget(source, entry("fin-collection-target", "Collections against target", "Payments received this month against the collection target.", "GaugeChart"), collection_target),
        CashflowWidget(source, entry("fin-cashflow", "Cash in and out", "Cash received against cash paid out for each of the last six months.", "LineChart")),
        PaymentsWidget(source, entry("fin-payments", "Recent payments", "The latest payments received from customers.", "DataTable")),
        ExpensesWidget(source, entry("fin-expenses", "Expenses by category", "How running costs over the last 90 days are shared between categories.", "DonutChart")),
    ]


def finance_catalog(source: FinanceSource, collection_target: Decimal) -> SourceCatalog:
    return SourceCatalog(source, lambda scoped: build_finance_widgets(scoped, collection_target))
