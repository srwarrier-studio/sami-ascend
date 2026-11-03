from datetime import date
from decimal import Decimal

from synapse_api.application.production_widgets import CAUSES, LOSS_DAYS, OUTPUT_DAYS, REASONS, downtime_by_cause, effectiveness, good_in, scrap_by_reason, since
from synapse_api.application.sales_summary import money
from synapse_api.domain.gateways.production_source import ProductionSource

PRODUCTION_IDS = {"prod-output", "prod-oee", "prod-plan", "prod-downtime", "prod-scrap", "prod-heat", "prod-orders"}
FACTORS = ["availability", "performance", "quality"]


class GetProductionSummary:
    def __init__(self, source: ProductionSource):
        self.source = source

    def execute(self, today: date, currency: str, show: set[str]) -> list[str]:
        sentences = [self.opening(today, currency)]
        if "prod-oee" in show:
            sentences.append(self.effectiveness(today, currency))
        if "prod-downtime" in show:
            sentences.append(self.downtime(today))
        if "prod-scrap" in show:
            sentences.append(self.scrap(today, currency))
        return [sentence for sentence in sentences if sentence]

    def opening(self, today: date, currency: str) -> str | None:
        rows = self.source.day_summaries(since(today, OUTPUT_DAYS * 2), today)
        now = good_in([row for row in rows if (today - row.day).days < OUTPUT_DAYS], currency)
        before = good_in([row for row in rows if (today - row.day).days >= OUTPUT_DAYS], currency)
        if now == 0 and before == 0:
            return None
        if before == 0:
            return f"Output over the last {OUTPUT_DAYS} days was {money(now, currency)}."
        change = (now - before) / before
        if round(abs(change) * 100, 1) == 0:
            return f"Output over the last {OUTPUT_DAYS} days was {money(now, currency)}, level with the {OUTPUT_DAYS} days before."
        return f"Output over the last {OUTPUT_DAYS} days was {money(now, currency)}, {'up' if change >= 0 else 'down'} {abs(change) * 100:.1f}% on the {OUTPUT_DAYS} days before."

    def effectiveness(self, today: date, currency: str) -> str | None:
        factors = effectiveness(self.source.day_summaries(since(today, OUTPUT_DAYS), today), currency)
        if factors is None:
            return None
        weakest = FACTORS[min(range(3), key=lambda index: factors[index])]
        return f"Equipment effectiveness is {factors[0] * factors[1] * factors[2] * 100:.0f}% over the last {OUTPUT_DAYS} days, held back most by {weakest}."

    def downtime(self, today: date) -> str | None:
        totals = downtime_by_cause(self.source, today)
        if not totals:
            return None
        cause, hours = max(totals.items(), key=lambda item: (item[1], item[0]))
        return f"{CAUSES.get(cause, cause)} caused the most downtime in the last {LOSS_DAYS} days: {hours:.0f} hours."

    def scrap(self, today: date, currency: str) -> str | None:
        totals = scrap_by_reason(self.source, today, currency)
        whole = sum(totals.values(), Decimal(0))
        if whole <= 0:
            return None
        reason, value = max(totals.items(), key=lambda item: (item[1], item[0]))
        return f"{REASONS.get(reason, reason)} caused the most scrap in the last {LOSS_DAYS} days: {money(value, currency)} ({value / whole * 100:.0f}% of scrapped output)."
