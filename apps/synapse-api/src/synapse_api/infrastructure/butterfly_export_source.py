from datetime import date
from decimal import Decimal

from synapse_api.domain.entities.exports import DestinationExport, ExportDay, ModeExport, TransitShipment
from synapse_api.domain.gateways.export_source import ExportSource
from synapse_api.infrastructure.butterfly_purchase_source import day_range
from synapse_api.infrastructure.odata_reader import ODataReader, company_clause


class ButterflyExportSource(ExportSource):
    def __init__(self, reader: ODataReader, companies: tuple[str, ...] | None = None):
        self.reader = reader
        self.companies = companies

    def for_companies(self, companies: tuple[str, ...]) -> "ButterflyExportSource":
        return ButterflyExportSource(self.reader, companies)

    def company(self) -> str:
        return company_clause("CompanyCode", self.companies)

    def window(self, entity: str, order: str, start: date, end: date) -> list[dict]:
        return self.reader.all_rows(f"{entity}?$filter={day_range('ShipmentDate', start, end)}{self.company()}&$orderby={order}")

    def day_summaries(self, start: date, end: date) -> list[ExportDay]:
        rows = self.window("ExportSummaryByDay", "ShipmentDate,Currency,CompanyCode", start, end)
        return [ExportDay(date.fromisoformat(r["ShipmentDate"]), r["ShipmentCount"], Decimal(r["NetAmount"]), r["Currency"]) for r in rows]

    def destination_summaries(self, start: date, end: date) -> list[DestinationExport]:
        rows = self.window("ExportSummaryByDestination", "ShipmentDate,Country,Currency,CompanyCode", start, end)
        return [DestinationExport(date.fromisoformat(r["ShipmentDate"]), r["Country"], r["CountryName"] or r["Country"], r["ShipmentCount"], Decimal(r["NetAmount"]), r["Currency"]) for r in rows]

    def mode_summaries(self, start: date, end: date) -> list[ModeExport]:
        rows = self.window("ExportSummaryByMode", "ShipmentDate,TransportMode,CompanyCode", start, end)
        return [ModeExport(date.fromisoformat(r["ShipmentDate"]), r["TransportMode"], r["ShipmentCount"]) for r in rows]

    def in_transit(self, top: int) -> list[TransitShipment]:
        path = f"ExportShipment?$filter=ShipmentStatus%20eq%20'T'{self.company()}&$orderby=ExpectedArrivalDate,Shipment&$top={top}"
        return [
            TransitShipment(r["Shipment"], r["CountryName"] or r["Country"], date.fromisoformat(r["ExpectedArrivalDate"]), Decimal(r["NetAmount"]), r["Currency"])
            for r in self.reader.get_rows(path)
        ]
