from datetime import date
from decimal import Decimal

from synapse_api.application.sales_summary import money
from synapse_api.application.source_catalog import TOP, SourceCatalog
from synapse_api.domain.entities.catalog import CatalogEntry
from synapse_api.domain.gateways.receivables_source import ReceivablesSource

BUCKETS = [("current", "Not due"), ("1-30", "1-30 days"), ("31-60", "31-60 days"), ("61-90", "61-90 days"), ("90+", "90+ days")]


class ReceivablesOutstandingWidget:
    def __init__(self, source: ReceivablesSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        rows = [row for row in self.source.totals(today) if row.currency == currency]
        open_amount = sum((row.open_amount for row in rows), Decimal(0))
        overdue = sum((row.overdue_amount for row in rows), Decimal(0))
        return {"title": self.entry.title, "measure": "receivables", "value": float(open_amount), "valueFormat": "currency", "caption": f"{money(overdue, currency)} overdue"}


class AgeingWidget:
    def __init__(self, source: ReceivablesSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        totals: dict[str, Decimal] = {}
        for row in self.source.ageing(today):
            if row.currency == currency:
                totals[row.bucket] = totals.get(row.bucket, Decimal(0)) + row.open_amount
        return {"title": self.entry.title, "measure": "receivables", "valueFormat": "currency", "data": [{"label": label, "value": float(totals.get(code, Decimal(0)))} for code, label in BUCKETS]}


class MostOverdueWidget:
    def __init__(self, source: ReceivablesSource, entry: CatalogEntry):
        self.source = source
        self.entry = entry

    def props(self, today: date, currency: str, top: int = TOP) -> dict:
        totals: dict[str, tuple[str, Decimal]] = {}
        for row in self.source.by_customer(today):
            if row.currency == currency and row.overdue_amount > 0:
                name, amount = totals.get(row.customer, (row.name, Decimal(0)))
                totals[row.customer] = (name, amount + row.overdue_amount)
        ranked = sorted(totals.items(), key=lambda item: (-item[1][1], item[0]))[:top]
        return {"title": self.entry.title, "measure": "overdue amount", "valueFormat": "currency", "items": [{"label": name, "value": float(amount)} for _, (name, amount) in ranked]}


def build_receivables_widgets(source: ReceivablesSource) -> list:
    def entry(id: str, title: str, description: str, widget: str) -> CatalogEntry:
        return CatalogEntry(id, title, description, "Finance", widget)

    return [
        ReceivablesOutstandingWidget(source, entry("fin-receivables", "Receivables outstanding", "Invoice amount not yet collected today, with the part that is past its due date.", "KpiCard")),
        AgeingWidget(source, entry("fin-ageing", "Receivables ageing", "Outstanding invoices grouped by how long they are past due.", "BarChart")),
        MostOverdueWidget(source, entry("fin-overdue", "Most overdue accounts", "Customers with the highest overdue balance.", "RankedList")),
    ]


def receivables_catalog(source: ReceivablesSource) -> SourceCatalog:
    return SourceCatalog(source, build_receivables_widgets)
