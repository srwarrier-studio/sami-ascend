from datetime import date, timedelta
from decimal import Decimal

from synapse_api.application.sales_widgets import MONTH_NAMES, TOP, Period, SalesKpiWidget, month_note, month_periods
from synapse_api.application.source_catalog import SourceCatalog
from synapse_api.domain.entities.catalog import CatalogEntry
from synapse_api.domain.gateways.purchase_source import PurchaseSource

STATUS = {"O": "Open", "D": "Delivered"}
TREND_MONTHS = 12
KPI_TREND_MONTHS = 6
ON_TIME_TARGET = 1.0
ON_TIME_DAYS = 90
CATEGORY_MONTHS = 3
CATEGORY_MONTHS_CHART = 6


def month_totals(source: PurchaseSource, today: date, months: int, currency: str) -> list[tuple[date, float]]:
    first = today.replace(day=1)
    index = first.year * 12 + first.month - 1 - (months - 1)
    start = date(index // 12, index % 12 + 1, 1)
    sums: dict[tuple[int, int], Decimal] = {}
    for row in source.daily_purchases(start, today):
        if row.currency == currency:
            key = (row.date.year, row.date.month)
            sums[key] = sums.get(key, Decimal(0)) + row.net_amount
    return [(date((i := index + n) // 12, i % 12 + 1, 1), float(sums.get(((index + n) // 12, (index + n) % 12 + 1), Decimal(0)))) for n in range(months)]


class PurchaseSpendWidget(SalesKpiWidget):
    measure = "purchases"

    def amount(self, period: Period, currency: str) -> Decimal:
        return sum((row.net_amount for row in self.source.daily_purchases(*period) if row.currency == currency), Decimal(0))


class PurchaseOpenWidget:
    def __init__(self, source: PurchaseSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        return {"title": self.entry.title, "measure": "purchase orders", "value": self.source.open_item_count(), "valueFormat": "number", "caption": "items not fully received"}


class PurchaseTrendWidget:
    def __init__(self, source: PurchaseSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        data = [{"label": MONTH_NAMES[month.month - 1], "value": value} for month, value in month_totals(self.source, today, TREND_MONTHS, currency)]
        return {"title": self.entry.title, "measure": "purchases", "valueFormat": "currency", "data": data}


class PurchaseVendorsWidget:
    def __init__(self, source: PurchaseSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        totals: dict[str, tuple[str, Decimal]] = {}
        for row in self.source.supplier_purchases(today.replace(day=1), today):
            if row.currency == currency:
                name, amount = totals.get(row.supplier, (row.name, Decimal(0)))
                totals[row.supplier] = (name, amount + row.net_amount)
        ranked = sorted(totals.items(), key=lambda item: (-item[1][1], item[0]))[:top]
        return {"title": self.entry.title, "measure": "purchases", "valueFormat": "currency", "items": [{"label": name, "value": float(amount)} for _, (name, amount) in ranked]}


class PurchaseRecentWidget:
    def __init__(self, source: PurchaseSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        items = [item for item in self.source.recent_items(top) if item.currency == currency]
        return {
            "title": self.entry.title,
            "columns": [
                {"key": "po", "label": "PO"},
                {"key": "vendor", "label": "Vendor"},
                {"key": "status", "label": "Status", "format": "status"},
                {"key": "amount", "label": "Amount", "format": "currency"},
            ],
            "rows": [{"po": f"{item.order}/{item.item}", "vendor": item.supplier_name, "status": STATUS.get(item.status, item.status), "amount": float(item.net_amount)} for item in items],
        }


class OnTimeDeliveryWidget:
    def __init__(self, source: PurchaseSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        due = [item for item in self.source.items_due(today - timedelta(days=ON_TIME_DAYS), today) if item.currency == currency]
        on_time = sum(1 for item in due if item.actual is not None and item.actual <= item.promised)
        share = on_time / len(due) if due else 0.0
        caption = f"last {ON_TIME_DAYS} days" if due else f"nothing due in {ON_TIME_DAYS} days"
        return {"title": self.entry.title, "measure": "on-time deliveries", "value": share, "target": ON_TIME_TARGET, "valueFormat": "percent", "caption": caption}


class CategoryDonutWidget:
    def __init__(self, source: PurchaseSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        totals = category_totals(self.source, today, currency)
        slices = [{"label": name, "value": float(value)} for name, value in sorted(totals.values(), key=lambda item: (-item[1], item[0])) if value > 0]
        return {"title": self.entry.title, "measure": "purchases", "slices": slices}


class CategoryByMonthWidget:
    def __init__(self, source: PurchaseSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        first = months_start(today, CATEGORY_MONTHS_CHART - 1)
        sums: dict[tuple[str, int, int], Decimal] = {}
        names: dict[str, str] = {}
        for row in self.source.group_purchases(first, today):
            if row.currency == currency:
                names[row.group] = row.name
                key = (row.group, row.date.year, row.date.month)
                sums[key] = sums.get(key, Decimal(0)) + row.net_amount
        months = [(first.year * 12 + first.month - 1 + n) for n in range(CATEGORY_MONTHS_CHART)]
        series = []
        for group in sorted(names):
            values = [sums.get((group, index // 12, index % 12 + 1), Decimal(0)) for index in months]
            if any(value > 0 for value in values):
                series.append({"name": names[group], "data": [{"label": MONTH_NAMES[index % 12], "value": float(value)} for index, value in zip(months, values)]})
        return {"title": self.entry.title, "measure": "purchases", "valueFormat": "currency", "series": series}


def months_start(today: date, back: int) -> date:
    index = today.year * 12 + today.month - 1 - back
    return date(index // 12, index % 12 + 1, 1)


def category_totals(source: PurchaseSource, today: date, currency: str) -> dict[str, tuple[str, Decimal]]:
    totals: dict[str, tuple[str, Decimal]] = {}
    for row in source.group_purchases(months_start(today, CATEGORY_MONTHS - 1), today):
        if row.currency == currency:
            name, value = totals.get(row.group, (row.name, Decimal(0)))
            totals[row.group] = (name, value + row.net_amount)
    return totals


def trend_for(source: PurchaseSource):
    def monthly(today: date, currency: str) -> list[float]:
        return [value for _, value in month_totals(source, today, KPI_TREND_MONTHS, currency)]

    return monthly


def build_purchase_widgets(source: PurchaseSource) -> list:
    def entry(id: str, title: str, description: str, widget: str) -> CatalogEntry:
        return CatalogEntry(id, title, description, "Purchase", widget)

    return [
        PurchaseSpendWidget(source, entry("pur-spend", "Purchases this month", "Purchase order value raised since the 1st of this month against the same days last month.", "KpiCard"), month_periods, trend_for(source), month_note),
        PurchaseOpenWidget(source, entry("pur-open", "Open purchase orders", "Purchase order items not yet fully received.", "KpiCard")),
        PurchaseTrendWidget(source, entry("pur-trend", "Purchase spend trend", "Purchase order value for each of the last twelve months.", "AreaChart")),
        PurchaseVendorsWidget(source, entry("pur-vendors", "Top vendors", "Suppliers ranked by purchase order value this month.", "RankedList")),
        PurchaseRecentWidget(source, entry("pur-recent", "Recent purchase orders", "The latest purchase order items and where they stand.", "DataTable")),
        OnTimeDeliveryWidget(source, entry("pur-ontime", "On-time delivery", "Share of purchase order items due this month that arrived by the promised date.", "GaugeChart")),
        CategoryDonutWidget(source, entry("pur-categories", "Spend by category", "How purchase value is shared between material groups over the last three months.", "DonutChart")),
        CategoryByMonthWidget(source, entry("pur-by-category-month", "Spend by category per month", "Purchase value each month split by material group.", "StackedBarChart")),
    ]


def purchase_catalog(source: PurchaseSource) -> SourceCatalog:
    return SourceCatalog(source, build_purchase_widgets)
