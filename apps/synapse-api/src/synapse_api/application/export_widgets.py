from datetime import date, timedelta
from decimal import Decimal

from synapse_api.application.sales_widgets import MONTH_NAMES, TOP, Period, SalesKpiWidget, month_note, month_periods
from synapse_api.application.source_catalog import SourceCatalog
from synapse_api.domain.entities.catalog import CatalogEntry
from synapse_api.domain.gateways.export_source import ExportSource

MIX_DAYS = 90
CALENDAR_DAYS = 365
TREND_MONTHS = 6
MODES = {"S": "Sea", "A": "Air", "R": "Road"}


def months_start(today: date, back: int) -> date:
    index = today.year * 12 + today.month - 1 - back
    return date(index // 12, index % 12 + 1, 1)


def monthly(source: ExportSource, today: date, currency: str, value) -> list[tuple[int, Decimal]]:
    first = months_start(today, TREND_MONTHS - 1)
    sums: dict[tuple[int, int], Decimal] = {}
    for row in source.day_summaries(first, today):
        if row.currency == currency:
            key = (row.day.year, row.day.month)
            sums[key] = sums.get(key, Decimal(0)) + value(row)
    base = first.year * 12 + first.month - 1
    return [(base + n, sums.get(((base + n) // 12, (base + n) % 12 + 1), Decimal(0))) for n in range(TREND_MONTHS)]


class ExportRevenueWidget(SalesKpiWidget):
    measure = "export revenue"

    def amount(self, period: Period, currency: str) -> Decimal:
        return sum((row.amount for row in self.source.day_summaries(*period) if row.currency == currency), Decimal(0))


class ExportShipmentsWidget(SalesKpiWidget):
    measure = "shipments"
    value_format = "number"

    def amount(self, period: Period, currency: str) -> Decimal:
        return Decimal(sum(row.count for row in self.source.day_summaries(*period) if row.currency == currency))


class RevenueTrendWidget:
    def __init__(self, source: ExportSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        data = [{"label": MONTH_NAMES[index % 12], "value": float(value)} for index, value in monthly(self.source, today, currency, lambda row: row.amount)]
        return {"title": self.entry.title, "measure": "export revenue", "valueFormat": "currency", "data": data}


def destination_totals(source: ExportSource, today: date, currency: str) -> dict[str, tuple[str, Decimal]]:
    totals: dict[str, tuple[str, Decimal]] = {}
    for row in source.destination_summaries(today - timedelta(days=MIX_DAYS - 1), today):
        if row.currency == currency:
            name, amount = totals.get(row.country, (row.name, Decimal(0)))
            totals[row.country] = (name, amount + row.amount)
    return totals


def mode_totals(source: ExportSource, today: date) -> dict[str, int]:
    totals: dict[str, int] = {}
    for row in source.mode_summaries(today - timedelta(days=MIX_DAYS - 1), today):
        totals[row.mode] = totals.get(row.mode, 0) + row.count
    return totals


class DestinationsWidget:
    def __init__(self, source: ExportSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        ranked = sorted(destination_totals(self.source, today, currency).values(), key=lambda item: (-item[1], item[0]))[:top]
        return {"title": self.entry.title, "measure": "export revenue", "valueFormat": "currency", "items": [{"label": name, "value": float(amount)} for name, amount in ranked]}


class ModesWidget:
    def __init__(self, source: ExportSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        totals = mode_totals(self.source, today)
        slices = [{"label": MODES.get(mode, mode), "value": count} for mode, count in sorted(totals.items(), key=lambda item: (-item[1], item[0])) if count > 0]
        return {"title": self.entry.title, "measure": "shipments", "slices": slices}


class TransitWidget:
    def __init__(self, source: ExportSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        shipments = [shipment for shipment in self.source.in_transit(top) if shipment.currency == currency]
        return {
            "title": self.entry.title,
            "columns": [
                {"key": "shipment", "label": "Shipment"},
                {"key": "destination", "label": "Destination"},
                {"key": "status", "label": "Status", "format": "status"},
                {"key": "value", "label": "Value", "format": "currency"},
            ],
            "rows": [
                {"shipment": s.shipment, "destination": s.destination, "status": "Late" if s.expected < today else "In transit", "value": float(s.amount)}
                for s in shipments
            ],
        }


class CalendarWidget:
    def __init__(self, source: ExportSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        counts: dict[date, int] = {}
        for row in self.source.day_summaries(today - timedelta(days=CALENDAR_DAYS - 1), today):
            if row.currency == currency:
                counts[row.day] = counts.get(row.day, 0) + row.count
        return {"title": self.entry.title, "measure": "shipments", "days": [{"date": day.isoformat(), "value": count} for day, count in sorted(counts.items()) if count > 0]}


def build_export_widgets(source: ExportSource) -> list:
    def entry(id: str, title: str, description: str, widget: str) -> CatalogEntry:
        return CatalogEntry(id, title, description, "Exports", widget)

    def trend(value):
        return lambda today, currency: [float(amount) for _, amount in monthly(source, today, currency, value)]

    return [
        ExportShipmentsWidget(source, entry("exp-shipments", "Shipments this month", "Export shipments dispatched so far this month against the same days last month.", "KpiCard"), month_periods, trend(lambda row: Decimal(row.count)), month_note),
        ExportRevenueWidget(source, entry("exp-revenue", "Export revenue", "Value of export shipments so far this month against the same days last month.", "KpiCard"), month_periods, trend(lambda row: row.amount), month_note),
        RevenueTrendWidget(source, entry("exp-trend", "Export revenue trend", "Export value for each of the last six months.", "AreaChart")),
        DestinationsWidget(source, entry("exp-destinations", "Top destinations", "Destination countries ranked by export value over the last 90 days.", "RankedList")),
        ModesWidget(source, entry("exp-modes", "Shipments by mode", "How shipments over the last 90 days are shared between sea, air and road.", "DonutChart")),
        TransitWidget(source, entry("exp-transit", "Shipments in transit", "Export shipments on their way, the earliest expected arrival first.", "DataTable")),
        CalendarWidget(source, entry("exp-calendar", "Shipments per day", "A year calendar showing which days shipments went out.", "CalendarHeatmapChart")),
    ]


def export_catalog(source: ExportSource) -> SourceCatalog:
    return SourceCatalog(source, build_export_widgets)
