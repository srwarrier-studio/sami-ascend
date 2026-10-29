import calendar
from collections.abc import Callable
from datetime import date, timedelta
from decimal import Decimal

from synapse_api.application.month_on_month_sales import GetMonthOnMonthSales
from synapse_api.application.period_sales import total_per_currency
from synapse_api.application.recent_high_value_orders import GetRecentHighValueOrders
from synapse_api.application.top_sales import GetTopCustomers, GetTopMaterials
from synapse_api.domain.entities.catalog import CatalogEntry
from synapse_api.domain.errors import CatalogEntryNotFound
from synapse_api.domain.gateways.sales_source import SalesSource
from synapse_api.domain.gateways.widget_catalog import WidgetCatalog

CURRENCY = "INR"
HIGH_VALUE_MINIMUM = Decimal(100000)
TOP = 5
MONTH_NAMES = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
ORDER_STATUS = {"A": "Open", "B": "In process", "C": "Completed"}

Period = tuple[date, date]


def same_day(year: int, month: int, day: int) -> date:
    return date(year, month, min(day, calendar.monthrange(year, month)[1]))


def today_periods(today: date) -> tuple[Period, Period]:
    yesterday = today - timedelta(days=1)
    return (today, today), (yesterday, yesterday)


def month_periods(today: date) -> tuple[Period, Period]:
    last = today.replace(day=1) - timedelta(days=1)
    return (today.replace(day=1), today), (last.replace(day=1), same_day(last.year, last.month, today.day))


def year_periods(today: date) -> tuple[Period, Period]:
    return (today.replace(month=1, day=1), today), (date(today.year - 1, 1, 1), same_day(today.year - 1, today.month, today.day))


def sales_in(source: SalesSource, period: Period) -> tuple[Decimal, int]:
    for total in total_per_currency(source, *period):
        if total.currency == CURRENCY:
            return total.net_amount, total.order_count
    return Decimal(0), 0


class SalesKpiWidget:
    def __init__(self, source: SalesSource, entry: CatalogEntry, caption: str, periods: Callable[[date], tuple[Period, Period]], trend: Callable[[date], list[float]]):
        self.source = source
        self.entry = entry
        self.caption = caption
        self.periods = periods
        self.trend = trend

    def props(self, today: date) -> dict:
        current, previous = self.periods(today)
        now, _ = sales_in(self.source, current)
        before, _ = sales_in(self.source, previous)
        props = {
            "title": self.entry.title,
            "measure": "sales",
            "value": float(now),
            "valueFormat": "currency",
            "caption": self.caption,
            "trend": self.trend(today),
        }
        if before:
            props["delta"] = float((now - before) / before)
        return props


class OrdersMonthWidget:
    def __init__(self, source: SalesSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date) -> dict:
        _, count = sales_in(self.source, month_periods(today)[0])
        return {"title": self.entry.title, "measure": "orders", "value": count, "caption": "since the 1st"}


class MonthOnMonthWidget:
    def __init__(self, source: SalesSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date) -> dict:
        months = GetMonthOnMonthSales(self.source).execute(today, 12)
        data = [{"label": MONTH_NAMES[m.month - 1], "value": float(m.net_amount)} for m in months if m.currency == CURRENCY]
        return {"title": self.entry.title, "measure": "sales", "valueFormat": "currency", "data": data}


class HighValueOrdersWidget:
    def __init__(self, source: SalesSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date) -> dict:
        orders = GetRecentHighValueOrders(self.source).execute(HIGH_VALUE_MINIMUM, TOP)
        return {
            "title": self.entry.title,
            "columns": [
                {"key": "order", "label": "Order"},
                {"key": "customer", "label": "Customer"},
                {"key": "status", "label": "Status", "format": "status"},
                {"key": "amount", "label": "Amount", "format": "currency"},
            ],
            "rows": [
                {"order": o.order, "customer": o.customer_name, "status": ORDER_STATUS.get(o.status, o.status), "amount": float(o.net_amount)}
                for o in orders
                if o.currency == CURRENCY
            ],
        }


class TopCustomersWidget:
    def __init__(self, source: SalesSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date) -> dict:
        ranked = GetTopCustomers(self.source).execute(today, TOP)
        items = [{"label": r.name, "value": float(r.net_amount)} for r in ranked if r.currency == CURRENCY]
        return {"title": self.entry.title, "measure": "sales", "valueFormat": "currency", "items": items}


class TopMaterialsWidget:
    def __init__(self, source: SalesSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date) -> dict:
        ranked = GetTopMaterials(self.source).execute(today, TOP)
        items = [{"label": r.description, "value": float(r.net_amount)} for r in ranked if r.currency == CURRENCY]
        return {"title": self.entry.title, "measure": "sales", "valueFormat": "currency", "items": items}


class DaySalesWidget:
    def __init__(self, source: SalesSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date) -> dict:
        this_month, last_month = month_periods(today)[0][0], month_periods(today)[1][0]
        totals = {row.date: float(row.net_amount) for row in self.source.daily_sales(last_month, today) if row.currency == CURRENCY}

        def points(first: date, last: date) -> list[dict]:
            return [{"label": str(day), "value": totals.get(first.replace(day=day), 0.0)} for day in range(1, last.day + 1)]

        last_days = this_month - timedelta(days=1)
        return {
            "title": self.entry.title,
            "measure": "sales",
            "valueFormat": "currency",
            "data": points(this_month, today),
            "compare": points(last_month, last_days),
            "label": "This month",
            "compareLabel": "Last month",
        }


class MonthTargetWidget:
    def __init__(self, source: SalesSource, entry: CatalogEntry, target: Decimal):
        self.source = source
        self.entry = entry
        self.target = target

    def props(self, today: date) -> dict:
        now, _ = sales_in(self.source, month_periods(today)[0])
        return {"title": self.entry.title, "measure": "sales", "value": float(now), "target": float(self.target), "valueFormat": "currency", "caption": "this month"}


class StatusSplitWidget:
    def __init__(self, source: SalesSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date) -> dict:
        counts: dict[str, int] = {}
        for row in self.source.order_statuses(today.replace(day=1), today):
            counts[row.status] = counts.get(row.status, 0) + 1
        slices = []
        for code, name in ORDER_STATUS.items():
            if counts.get(code):
                slice_ = {"label": name, "value": counts[code]}
                if code == "C":
                    slice_["tone"] = "positive"
                slices.append(slice_)
        return {"title": self.entry.title, "measure": "orders", "slices": slices}


def entry(id: str, title: str, description: str, category: str, widget: str) -> CatalogEntry:
    return CatalogEntry(id, title, description, category, widget)


class SalesWidgetCatalog(WidgetCatalog):
    def __init__(self, source: SalesSource, month_target: Decimal):
        self.source = source
        self.month_target = month_target
        self.widgets = self.build(source)

    def build(self, source: SalesSource) -> list:
        def daily_trend(today: date) -> list[float]:
            totals = {row.date: float(row.net_amount) for row in source.daily_sales(today - timedelta(days=6), today) if row.currency == CURRENCY}
            return [totals.get(today - timedelta(days=back), 0.0) for back in range(6, -1, -1)]

        def monthly_trend(today: date) -> list[float]:
            months = GetMonthOnMonthSales(source).execute(today, 6)
            return [float(m.net_amount) for m in months if m.currency == CURRENCY]

        today_entry = entry("sales-today", "Sales today", "Net sales invoiced today against yesterday.", "Sales", "KpiCard")
        month_entry = entry("sales-month", "Sales this month", "Net sales since the 1st of this month against the same days last month.", "Sales", "KpiCard")
        year_entry = entry("sales-year", "Sales this year", "Net sales since the start of the year against the same period last year.", "Sales", "KpiCard")
        return [
            SalesKpiWidget(source, today_entry, "vs yesterday", today_periods, daily_trend),
            SalesKpiWidget(source, month_entry, "vs last month", month_periods, monthly_trend),
            SalesKpiWidget(source, year_entry, "vs last year", year_periods, monthly_trend),
            OrdersMonthWidget(source, entry("orders-month", "Orders this month", "Number of sales orders since the 1st of this month.", "Sales", "KpiCard")),
            MonthOnMonthWidget(source, entry("month-on-month", "Month-on-month sales", "Net sales for each of the last 12 months.", "Sales", "BarChart")),
            DaySalesWidget(source, entry("day-sales", "Day sales", "Net sales for each day of this month, with last month behind it.", "Sales", "LineChart")),
            HighValueOrdersWidget(source, entry("high-value-sales", "Recent high-value sales", "The latest sales orders above the high-value limit.", "Sales", "DataTable")),
            TopCustomersWidget(source, entry("top-customers", "Top customers", "Customers ranked by net sales this month.", "Sales", "RankedList")),
            TopMaterialsWidget(source, entry("top-materials", "Top materials", "Materials ranked by net sales this month.", "Inventory", "RankedList")),
            MonthTargetWidget(source, entry("month-target", "Month target", "Net sales this month against the monthly sales target.", "Sales", "GaugeChart"), self.month_target),
            StatusSplitWidget(source, entry("status-split", "Invoice status split", "Share of orders that are paid, open or overdue.", "Finance", "DonutChart")),
        ]

    def entries(self) -> list[CatalogEntry]:
        return [widget.entry for widget in self.widgets]

    def data(self, entry_id: str, today: date) -> dict:
        for widget in self.widgets:
            if widget.entry.id == entry_id:
                return widget.props(today)
        raise CatalogEntryNotFound(entry_id)
