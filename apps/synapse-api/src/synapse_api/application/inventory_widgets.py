from datetime import date, timedelta
from decimal import Decimal

from synapse_api.application.sales_widgets import MONTH_NAMES
from synapse_api.application.source_catalog import TOP, SourceCatalog
from synapse_api.domain.entities.catalog import CatalogEntry
from synapse_api.domain.gateways.inventory_source import InventorySource

TREND_MONTHS = 6
MOVEMENT_DAYS = 14
HEAT_DAYS = 90
WEEKDAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
STATUS_NAMES = {"Z": "Out of stock", "L": "Low"}


def period_of(day: date) -> str:
    return f"{day.year}-{day.month:02d}"


def months_back(today: date, count: int) -> date:
    index = today.year * 12 + today.month - 1 - count
    return date(index // 12, index % 12 + 1, 1)


def month_values(source: InventorySource, today: date, currency: str) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for month in source.month_values(period_of(months_back(today, TREND_MONTHS - 1))):
        if month.currency == currency:
            totals[month.period] = totals.get(month.period, Decimal(0)) + month.value
    return dict(sorted(totals.items()))


def stock_value(source: InventorySource, currency: str) -> Decimal:
    return sum((row.value for row in source.stock_by_warehouse() if row.currency == currency), Decimal(0))


def hour_label(hour: int) -> str:
    return f"{hour % 12 or 12}{'am' if hour < 12 else 'pm'}"


class StockValueWidget:
    def __init__(self, source: InventorySource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        now = stock_value(self.source, currency)
        months = month_values(self.source, today, currency)
        last_month_end = today.replace(day=1) - timedelta(days=1)
        before = months.get(period_of(last_month_end), Decimal(0))
        props = {
            "title": self.entry.title,
            "measure": "stock value",
            "value": float(now),
            "valueFormat": "currency",
            "caption": f"vs {last_month_end.day} {MONTH_NAMES[last_month_end.month - 1]}",
            "trend": [float(value) for value in months.values()],
        }
        if before > 0:
            props["delta"] = float((now - before) / before)
        return props


class ItemsBelowReorderWidget:
    def __init__(self, source: InventorySource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        rows = [row for row in self.source.stock_by_status() if row.currency == currency]
        low = sum(row.count for row in rows if row.status in STATUS_NAMES)
        out = sum(row.count for row in rows if row.status == "Z")
        return {"title": self.entry.title, "measure": "items", "value": low, "valueFormat": "number", "caption": f"{out} out of stock" if out else "none out of stock"}


class AvailabilityWidget:
    def __init__(self, source: InventorySource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        rows = [row for row in self.source.stock_by_status() if row.currency == currency]
        total = sum(row.count for row in rows)
        in_stock = total - sum(row.count for row in rows if row.status == "Z")
        return {"title": self.entry.title, "measure": "availability", "value": in_stock / total if total else 0.0, "target": 1.0, "valueFormat": "percent", "caption": "items in stock"}


class WarehouseStockWidget:
    def __init__(self, source: InventorySource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        rows = [row for row in self.source.stock_by_warehouse() if row.currency == currency]
        several = len({row.plant for row in rows}) > 1
        totals: dict[tuple[str, str], tuple[str, Decimal]] = {}
        for row in rows:
            name, value = totals.get((row.plant, row.location), (row.name, Decimal(0)))
            totals[(row.plant, row.location)] = (name, value + row.value)
        data = [{"label": f"{name} ({plant})" if several else name, "value": float(value)} for (plant, _), (name, value) in sorted(totals.items())]
        return {"title": self.entry.title, "measure": "stock value", "valueFormat": "currency", "data": data}


class GroupStockWidget:
    def __init__(self, source: InventorySource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        totals: dict[str, tuple[str, Decimal]] = {}
        for row in self.source.stock_by_group():
            if row.currency == currency:
                name, value = totals.get(row.group, (row.name, Decimal(0)))
                totals[row.group] = (name, value + row.value)
        ranked = sorted((item for item in totals.values() if item[1] > 0), key=lambda item: (-item[1], item[0]))
        return {"title": self.entry.title, "measure": "stock value", "slices": [{"label": name, "value": float(value)} for name, value in ranked]}


class SlowMovingWidget:
    def __init__(self, source: InventorySource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        items = [item for item in self.source.idle_items(top) if item.currency == currency and item.last_movement is not None]
        ranked = sorted(((item.description, (today - item.last_movement).days) for item in items), key=lambda pair: (-pair[1], pair[0]))
        return {"title": self.entry.title, "measure": "idle days", "valueFormat": "number", "items": [{"label": name, "value": days} for name, days in ranked]}


class MovementWidget:
    def __init__(self, source: InventorySource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        first = today - timedelta(days=MOVEMENT_DAYS - 1)
        receipts: dict[date, Decimal] = {}
        issues: dict[date, Decimal] = {}
        for row in self.source.movements_by_day(first, today):
            if row.currency == currency:
                receipts[row.day] = receipts.get(row.day, Decimal(0)) + row.receipts
                issues[row.day] = issues.get(row.day, Decimal(0)) + row.issues
        days = [first + timedelta(days=n) for n in range(MOVEMENT_DAYS)]

        def points(values: dict[date, Decimal]) -> list[dict]:
            return [{"label": f"{day.day} {MONTH_NAMES[day.month - 1]}", "value": float(values.get(day, Decimal(0)))} for day in days]

        return {"title": self.entry.title, "measure": "goods movements", "valueFormat": "currency", "data": points(receipts), "compare": points(issues), "label": "Receipts", "compareLabel": "Issues"}


class ReorderListWidget:
    def __init__(self, source: InventorySource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        items = [item for item in self.source.low_items() if item.currency == currency]
        ranked = sorted(items, key=lambda item: (item.status != "Z", item.quantity / item.reorder_level if item.reorder_level else Decimal(0), item.material))[:top]
        return {
            "title": self.entry.title,
            "columns": [
                {"key": "material", "label": "Material"},
                {"key": "stock", "label": "In stock", "format": "number"},
                {"key": "level", "label": "Reorder at", "format": "number"},
                {"key": "status", "label": "Status", "format": "status"},
            ],
            "rows": [{"material": item.description, "stock": float(item.quantity), "level": float(item.reorder_level), "status": STATUS_NAMES.get(item.status, item.status)} for item in ranked],
        }


class MovementHeatWidget:
    def __init__(self, source: InventorySource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        counts: dict[tuple[int, int], int] = {}
        for row in self.source.movements_by_hour(today - timedelta(days=HEAT_DAYS - 1), today):
            key = (row.day.weekday(), row.hour)
            counts[key] = counts.get(key, 0) + row.count
        cells = [{"row": WEEKDAYS[weekday], "column": hour_label(hour), "value": count} for (weekday, hour), count in sorted(counts.items()) if count > 0]
        return {"title": self.entry.title, "measure": "movements", "cells": cells}


def build_inventory_widgets(source: InventorySource) -> list:
    def entry(id: str, title: str, description: str, widget: str) -> CatalogEntry:
        return CatalogEntry(id, title, description, "Inventory", widget)

    return [
        StockValueWidget(source, entry("inv-value", "Stock value", "Value of all stock on hand, against the end of last month.", "KpiCard")),
        ItemsBelowReorderWidget(source, entry("inv-low", "Items below reorder level", "Materials whose stock is below the reorder level or at zero.", "KpiCard")),
        AvailabilityWidget(source, entry("inv-availability", "Stock availability", "Share of stocked materials that currently have stock.", "GaugeChart")),
        WarehouseStockWidget(source, entry("inv-warehouses", "Stock by warehouse", "Stock value held in each storage location.", "BarChart")),
        GroupStockWidget(source, entry("inv-groups", "Stock by material group", "How stock value is shared between material groups.", "DonutChart")),
        SlowMovingWidget(source, entry("inv-slow", "Slow-moving materials", "Materials in stock that have not moved for the longest time.", "RankedList")),
        MovementWidget(source, entry("inv-movement", "Receipts and issues", "Goods received against goods issued for each of the last 14 days, in value.", "LineChart")),
        ReorderListWidget(source, entry("inv-reorder", "Reorder list", "Materials to reorder now, out of stock first.", "DataTable")),
        MovementHeatWidget(source, entry("inv-heat", "Goods movement by weekday and hour", "When goods are received and issued through the week, over the last 90 days.", "HeatmapChart")),
    ]


def inventory_catalog(source: InventorySource) -> SourceCatalog:
    return SourceCatalog(source, build_inventory_widgets)
