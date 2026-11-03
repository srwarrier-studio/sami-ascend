from decimal import Decimal

from butterfly.domain.entities.exports import ExportSummaryByDay, ExportSummaryByDestination, ExportSummaryByMode
from butterfly.domain.repositories.export_repo import ExportRepo

ZERO = Decimal("0.00")


class SummarizeExports:
    def __init__(self, repo: ExportRepo):
        self.repo = repo

    def by_day(self) -> list[ExportSummaryByDay]:
        totals: dict[tuple, list] = {}
        for s in self.repo.shipments():
            entry = totals.setdefault((s.shipment_date, s.currency, s.company_code), [0, ZERO])
            entry[0] += 1
            entry[1] += s.net_amount
        return [ExportSummaryByDay(day, count, amount, currency, company) for (day, currency, company), (count, amount) in sorted(totals.items())]

    def by_destination(self) -> list[ExportSummaryByDestination]:
        totals: dict[tuple, list] = {}
        for s in self.repo.shipments():
            entry = totals.setdefault((s.shipment_date, s.country, s.currency, s.company_code), [s.country_name, 0, ZERO])
            entry[1] += 1
            entry[2] += s.net_amount
        return [ExportSummaryByDestination(day, country, name, count, amount, currency, company) for (day, country, currency, company), (name, count, amount) in sorted(totals.items())]

    def by_mode(self) -> list[ExportSummaryByMode]:
        totals: dict[tuple, int] = {}
        for s in self.repo.shipments():
            key = (s.shipment_date, s.transport_mode, s.company_code)
            totals[key] = totals.get(key, 0) + 1
        return [ExportSummaryByMode(day, mode, count, company) for (day, mode, company), count in sorted(totals.items())]
