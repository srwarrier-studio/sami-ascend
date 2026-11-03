from decimal import Decimal

from butterfly.domain.entities.production import DowntimeSummaryByDay, OutputSummaryByLineShift, ProductionSummaryByDay, ScrapSummaryByDay
from butterfly.domain.repositories.production_repo import ProductionRepo

ZERO = Decimal("0.00")


class SummarizeProduction:
    def __init__(self, repo: ProductionRepo):
        self.repo = repo

    def by_day(self) -> list[ProductionSummaryByDay]:
        hours: dict[tuple, Decimal] = {}
        for downtime in self.repo.downtimes():
            key = (downtime.posting_date, downtime.company_code)
            hours[key] = hours.get(key, ZERO) + downtime.downtime_hours
        totals: dict[tuple, list] = {}
        for c in self.repo.confirmations():
            entry = totals.setdefault((c.posting_date, c.currency, c.company_code), [ZERO, ZERO, ZERO, ZERO, 0])
            entry[0] += c.run_hours
            entry[1] += c.target_value
            entry[2] += c.yield_value
            entry[3] += c.scrap_value
            entry[4] += 1
        return [
            ProductionSummaryByDay(day, planned, hours.get((day, company), ZERO), target, good, scrap, count, currency, company)
            for (day, currency, company), (planned, target, good, scrap, count) in sorted(totals.items())
        ]

    def downtime_by_day(self) -> list[DowntimeSummaryByDay]:
        totals: dict[tuple, list] = {}
        for d in self.repo.downtimes():
            entry = totals.setdefault((d.posting_date, d.downtime_cause, d.company_code), [ZERO, 0])
            entry[0] += d.downtime_hours
            entry[1] += 1
        return [DowntimeSummaryByDay(day, cause, hours, count, company) for (day, cause, company), (hours, count) in sorted(totals.items())]

    def scrap_by_day(self) -> list[ScrapSummaryByDay]:
        totals: dict[tuple, list] = {}
        for c in self.repo.confirmations():
            if c.scrap_reason is not None:
                entry = totals.setdefault((c.posting_date, c.scrap_reason, c.currency, c.company_code), [ZERO, 0])
                entry[0] += c.scrap_value
                entry[1] += 1
        return [ScrapSummaryByDay(day, reason, value, count, currency, company) for (day, reason, currency, company), (value, count) in sorted(totals.items())]

    def output_by_line_shift(self) -> list[OutputSummaryByLineShift]:
        totals: dict[tuple, list] = {}
        for c in self.repo.confirmations():
            entry = totals.setdefault((c.posting_date, c.work_center, c.shift, c.currency, c.company_code), [c.work_center_name, ZERO])
            entry[1] += c.yield_value
        return [OutputSummaryByLineShift(day, line, shift, name, value, currency, company) for (day, line, shift, currency, company), (name, value) in sorted(totals.items())]
