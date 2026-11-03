from datetime import date
from decimal import Decimal

from synapse_api.application.export_widgets import MIX_DAYS, MODES, destination_totals, mode_totals
from synapse_api.application.sales_summary import headline, money
from synapse_api.application.sales_widgets import month_periods
from synapse_api.domain.gateways.export_source import ExportSource

EXPORT_IDS = {"exp-shipments", "exp-revenue", "exp-trend", "exp-destinations", "exp-modes", "exp-transit", "exp-calendar"}


class GetExportSummary:
    def __init__(self, source: ExportSource):
        self.source = source

    def execute(self, today: date, currency: str, show: set[str]) -> list[str]:
        sentences = [self.opening(today, currency)]
        if "exp-transit" in show:
            sentences.append(self.transit(today, currency))
        if "exp-destinations" in show:
            sentences.append(self.top_destination(today, currency))
        if "exp-modes" in show:
            sentences.append(self.top_mode(today))
        return [sentence for sentence in sentences if sentence]

    def month(self, period: tuple[date, date], currency: str) -> tuple[int, Decimal]:
        rows = [row for row in self.source.day_summaries(*period) if row.currency == currency]
        return sum(row.count for row in rows), sum((row.amount for row in rows), Decimal(0))

    def opening(self, today: date, currency: str) -> str | None:
        current, previous = month_periods(today)
        count, now = self.month(current, currency)
        _, before = self.month(previous, currency)
        line = headline("Exports", today, current, previous, now, before, currency)
        return line.replace("Exports this month are ", f"Exports this month are {count} shipment{'' if count == 1 else 's'} worth ", 1) if line else None

    def transit(self, today: date, currency: str) -> str | None:
        shipments = [s for s in self.source.in_transit(1000) if s.currency == currency]
        if not shipments:
            return None
        late = sum(1 for s in shipments if s.expected < today)
        return f"{len(shipments)} shipments are in transit, {late} of them past their expected arrival." if len(shipments) > 1 else ("1 shipment is in transit" + (", past its expected arrival." if late else "."))

    def top_destination(self, today: date, currency: str) -> str | None:
        totals = destination_totals(self.source, today, currency)
        whole = sum((amount for _, amount in totals.values()), Decimal(0))
        if whole <= 0:
            return None
        name, amount = max(totals.values(), key=lambda item: (item[1], item[0]))
        return f"{name} is the top destination over the last {MIX_DAYS} days: {money(amount, currency)} ({amount / whole * 100:.0f}% of exports)."

    def top_mode(self, today: date) -> str | None:
        totals = mode_totals(self.source, today)
        whole = sum(totals.values())
        if whole <= 0:
            return None
        mode, count = max(totals.items(), key=lambda item: (item[1], item[0]))
        return f"{MODES.get(mode, mode)} carries {count / whole * 100:.0f}% of shipments over the last {MIX_DAYS} days."
