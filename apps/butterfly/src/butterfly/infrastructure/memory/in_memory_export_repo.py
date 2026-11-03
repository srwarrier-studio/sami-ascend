from butterfly.domain.entities.exports import ExportShipment
from butterfly.domain.repositories.export_repo import ExportRepo


class InMemoryExportRepo(ExportRepo):
    def __init__(self, shipments: list[ExportShipment] | None = None):
        self._shipments = shipments or []

    def shipments(self) -> list[ExportShipment]:
        return list(self._shipments)
