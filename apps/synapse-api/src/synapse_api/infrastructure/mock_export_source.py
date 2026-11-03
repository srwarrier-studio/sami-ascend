from datetime import date

from synapse_api.domain.entities.exports import DestinationExport, ExportDay, ModeExport, TransitShipment
from synapse_api.domain.gateways.export_source import ExportSource


class MockExportSource(ExportSource):
    def __init__(self, days: list[ExportDay] | None = None, destinations: list[DestinationExport] | None = None, modes: list[ModeExport] | None = None, transit: list[TransitShipment] | None = None):
        self.days = days or []
        self.destinations = destinations or []
        self.modes = modes or []
        self.transit = transit or []

    def for_companies(self, companies: tuple[str, ...]) -> "MockExportSource":
        return self

    def day_summaries(self, start: date, end: date) -> list[ExportDay]:
        return [row for row in self.days if start <= row.day <= end]

    def destination_summaries(self, start: date, end: date) -> list[DestinationExport]:
        return [row for row in self.destinations if start <= row.day <= end]

    def mode_summaries(self, start: date, end: date) -> list[ModeExport]:
        return [row for row in self.modes if start <= row.day <= end]

    def in_transit(self, top: int) -> list[TransitShipment]:
        return sorted(self.transit, key=lambda shipment: (shipment.expected, shipment.shipment))[:top]
