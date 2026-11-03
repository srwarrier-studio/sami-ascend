from datetime import date, timedelta
from decimal import Decimal

from synapse_api.application.sales_widgets import MONTH_NAMES
from synapse_api.application.source_catalog import TOP, SourceCatalog
from synapse_api.domain.entities.catalog import CatalogEntry
from synapse_api.domain.entities.production import ProductionDay
from synapse_api.domain.gateways.production_source import ProductionSource

OUTPUT_DAYS = 30
OUTPUT_WINDOWS = 6
LOSS_DAYS = 90
PLAN_MONTHS = 6
OEE_TARGET = 0.85
CAUSES = {"BREAKDOWN": "Breakdown", "CHANGEOVER": "Changeover", "NO_MATERIAL": "No material", "MAINTENANCE": "Maintenance", "OTHER": "Other"}
REASONS = {"MATERIAL_DEFECT": "Material defect", "MACHINE_SETTING": "Machine setting", "OPERATOR_ERROR": "Operator error", "OTHER": "Other"}
SHIFTS = [("M", "Morning"), ("A", "Afternoon"), ("N", "Night")]


def since(today: date, days: int) -> date:
    return today - timedelta(days=days - 1)


def good_in(rows: list[ProductionDay], currency: str) -> Decimal:
    return sum((row.good for row in rows if row.currency == currency), Decimal(0))


def effectiveness(rows: list[ProductionDay], currency: str) -> tuple[float, float, float] | None:
    rows = [row for row in rows if row.currency == currency]
    planned = sum((row.planned_hours for row in rows), Decimal(0))
    target = sum((row.target for row in rows), Decimal(0))
    good = sum((row.good for row in rows), Decimal(0))
    scrap = sum((row.scrap for row in rows), Decimal(0))
    if planned <= 0 or target <= 0 or good + scrap <= 0:
        return None
    down = sum((row.downtime_hours for row in rows), Decimal(0))
    return float(1 - down / planned), float((good + scrap) / target), float(good / (good + scrap))


def months_back(today: date, count: int) -> date:
    index = today.year * 12 + today.month - 1 - count
    return date(index // 12, index % 12 + 1, 1)


class OutputWidget:
    def __init__(self, source: ProductionSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        windows = [Decimal(0)] * OUTPUT_WINDOWS
        for row in self.source.day_summaries(since(today, OUTPUT_DAYS * OUTPUT_WINDOWS), today):
            if row.currency == currency:
                windows[(today - row.day).days // OUTPUT_DAYS] += row.good
        now, before = windows[0], windows[1]
        props = {
            "title": self.entry.title,
            "measure": "output",
            "value": float(now),
            "valueFormat": "currency",
            "caption": f"last {OUTPUT_DAYS} days vs the {OUTPUT_DAYS} before",
            "trend": [float(value) for value in reversed(windows)],
        }
        if before > 0:
            props["delta"] = float((now - before) / before)
        return props


class EffectivenessWidget:
    def __init__(self, source: ProductionSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        factors = effectiveness(self.source.day_summaries(since(today, OUTPUT_DAYS), today), currency)
        value = factors[0] * factors[1] * factors[2] if factors else 0.0
        caption = f"last {OUTPUT_DAYS} days" if factors else f"no production in {OUTPUT_DAYS} days"
        return {"title": self.entry.title, "measure": "effectiveness", "value": value, "target": OEE_TARGET, "valueFormat": "percent", "caption": caption}


class OutputAgainstPlanWidget:
    def __init__(self, source: ProductionSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        first = months_back(today, PLAN_MONTHS - 1)
        good: dict[tuple[int, int], Decimal] = {}
        plan: dict[tuple[int, int], Decimal] = {}
        for row in self.source.day_summaries(first, today):
            if row.currency == currency:
                key = (row.day.year, row.day.month)
                good[key] = good.get(key, Decimal(0)) + row.good
                plan[key] = plan.get(key, Decimal(0)) + row.target
        months = [(first.year * 12 + first.month - 1 + n) for n in range(PLAN_MONTHS)]

        def points(values: dict[tuple[int, int], Decimal]) -> list[dict]:
            return [{"label": MONTH_NAMES[index % 12], "value": float(values.get((index // 12, index % 12 + 1), Decimal(0)))} for index in months]

        return {"title": self.entry.title, "measure": "output", "valueFormat": "currency", "data": points(good), "compare": points(plan), "label": "Output", "compareLabel": "Plan"}


class DowntimeWidget:
    def __init__(self, source: ProductionSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        totals = downtime_by_cause(self.source, today)
        data = [{"label": CAUSES.get(cause, cause), "value": float(hours)} for cause, hours in sorted(totals.items(), key=lambda item: (-item[1], item[0]))]
        return {"title": self.entry.title, "measure": "downtime hours", "valueFormat": "number", "data": data}


class ScrapWidget:
    def __init__(self, source: ProductionSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        totals = scrap_by_reason(self.source, today, currency)
        slices = [{"label": REASONS.get(reason, reason), "value": float(value)} for reason, value in sorted(totals.items(), key=lambda item: (-item[1], item[0])) if value > 0]
        return {"title": self.entry.title, "measure": "scrap", "slices": slices}


class LineShiftHeatWidget:
    def __init__(self, source: ProductionSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        totals: dict[tuple[str, str], Decimal] = {}
        for row in self.source.line_shift_output(since(today, OUTPUT_DAYS), today):
            if row.currency == currency:
                totals[(row.name, row.shift)] = totals.get((row.name, row.shift), Decimal(0)) + row.good
        names = dict(SHIFTS)
        cells = [{"row": line, "column": names.get(shift, shift), "value": float(value)} for (line, shift), value in sorted(totals.items()) if value > 0]
        return {"title": self.entry.title, "measure": "output", "cells": cells}


class OpenOrdersWidget:
    def __init__(self, source: ProductionSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        def status(start: date, end: date) -> str:
            return "Planned" if start > today else "Late" if end < today else "In progress"

        return {
            "title": self.entry.title,
            "columns": [
                {"key": "order", "label": "Order"},
                {"key": "item", "label": "Item"},
                {"key": "status", "label": "Status", "format": "status"},
                {"key": "quantity", "label": "Quantity", "format": "number"},
            ],
            "rows": [{"order": o.order, "item": o.description, "status": status(o.start, o.end), "quantity": float(o.quantity)} for o in self.source.open_orders(top)],
        }


def downtime_by_cause(source: ProductionSource, today: date) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for row in source.downtime_summaries(since(today, LOSS_DAYS), today):
        totals[row.cause] = totals.get(row.cause, Decimal(0)) + row.hours
    return totals


def scrap_by_reason(source: ProductionSource, today: date, currency: str) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for row in source.scrap_summaries(since(today, LOSS_DAYS), today):
        if row.currency == currency:
            totals[row.reason] = totals.get(row.reason, Decimal(0)) + row.value
    return totals


def build_production_widgets(source: ProductionSource) -> list:
    def entry(id: str, title: str, description: str, widget: str) -> CatalogEntry:
        return CatalogEntry(id, title, description, "Production", widget)

    return [
        OutputWidget(source, entry("prod-output", "Output, last 30 days", "Good output value of the last 30 days against the 30 days before.", "KpiCard")),
        EffectivenessWidget(source, entry("prod-oee", "Equipment effectiveness", "Availability x performance x quality over the last 30 days, against the 85% target.", "GaugeChart")),
        OutputAgainstPlanWidget(source, entry("prod-plan", "Output against plan", "Good output for each of the last six months against the production plan.", "LineChart")),
        DowntimeWidget(source, entry("prod-downtime", "Downtime by cause", "Hours of work center stoppage over the last 90 days, grouped by cause.", "BarChart")),
        ScrapWidget(source, entry("prod-scrap", "Scrap by reason", "How scrapped output value over the last 90 days is shared between reasons.", "DonutChart")),
        LineShiftHeatWidget(source, entry("prod-heat", "Output by line and shift", "Good output of each line in each shift over the last 30 days.", "HeatmapChart")),
        OpenOrdersWidget(source, entry("prod-orders", "Open production orders", "Production orders released and not yet complete.", "DataTable")),
    ]


def production_catalog(source: ProductionSource) -> SourceCatalog:
    return SourceCatalog(source, build_production_widgets)
