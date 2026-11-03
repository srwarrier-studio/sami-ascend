from abc import ABC, abstractmethod

from butterfly.domain.entities.exports import ExportShipment


class ExportRepo(ABC):
    @abstractmethod
    def shipments(self) -> list[ExportShipment]: ...

    def listing(self, entity: str):
        return getattr(self, entity)()

    def summary_listing(self, name: str):
        return None
