from datetime import date
from decimal import Decimal

from synapse_api.domain.entities.production import DowntimeDay, LineShiftOutput, OpenOrder, ProductionDay, ScrapDay
from synapse_api.domain.gateways.production_source import ProductionSource
from synapse_api.infrastructure.butterfly_purchase_source import day_range
from synapse_api.infrastructure.odata_reader import ODataReader, company_clause


class ButterflyProductionSource(ProductionSource):
    def __init__(self, reader: ODataReader, orders: ODataReader, companies: tuple[str, ...] | None = None):
        self.reader = reader
        self.orders = orders
        self.companies = companies

    def for_companies(self, companies: tuple[str, ...]) -> "ButterflyProductionSource":
        return ButterflyProductionSource(self.reader, self.orders, companies)

    def company(self) -> str:
        return company_clause("CompanyCode", self.companies)

    def window(self, entity: str, order: str, start: date, end: date) -> list[dict]:
        return self.reader.all_rows(f"{entity}?$filter={day_range('PostingDate', start, end)}{self.company()}&$orderby={order}")

    def day_summaries(self, start: date, end: date) -> list[ProductionDay]:
        rows = self.window("ProductionSummaryByDay", "PostingDate,Currency,CompanyCode", start, end)
        return [
            ProductionDay(
                date.fromisoformat(r["PostingDate"]), Decimal(r["PlannedHours"]), Decimal(r["DowntimeHours"]), Decimal(r["TargetValue"]), Decimal(r["GoodValue"]),
                Decimal(r["ScrapValue"]), r["Currency"],
            )
            for r in rows
        ]

    def downtime_summaries(self, start: date, end: date) -> list[DowntimeDay]:
        rows = self.window("DowntimeSummaryByDay", "PostingDate,DowntimeCause,CompanyCode", start, end)
        return [DowntimeDay(date.fromisoformat(r["PostingDate"]), r["DowntimeCause"], Decimal(r["DowntimeHours"])) for r in rows]

    def scrap_summaries(self, start: date, end: date) -> list[ScrapDay]:
        rows = self.window("ScrapSummaryByDay", "PostingDate,ScrapReason,Currency,CompanyCode", start, end)
        return [ScrapDay(date.fromisoformat(r["PostingDate"]), r["ScrapReason"], Decimal(r["ScrapValue"]), r["Currency"]) for r in rows]

    def line_shift_output(self, start: date, end: date) -> list[LineShiftOutput]:
        rows = self.window("OutputSummaryByLineShift", "PostingDate,WorkCenter,Shift,Currency,CompanyCode", start, end)
        return [LineShiftOutput(date.fromisoformat(r["PostingDate"]), r["WorkCenter"], r["WorkCenterName"] or r["WorkCenter"], r["Shift"], Decimal(r["GoodValue"]), r["Currency"]) for r in rows]

    def open_orders(self, top: int) -> list[OpenOrder]:
        path = f"ProductionOrder?$filter=ProductionStatus%20eq%20'R'{self.company()}&$orderby=PlannedStartDate,ProductionOrder&$top={top}"
        return [
            OpenOrder(r["ProductionOrder"], r["MaterialDescription"] or r["Material"], Decimal(r["PlannedQuantity"]), date.fromisoformat(r["PlannedStartDate"]), date.fromisoformat(r["PlannedEndDate"]))
            for r in self.orders.get_rows(path)
        ]
