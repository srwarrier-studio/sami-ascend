from abc import ABC, abstractmethod
from datetime import date

from synapse_api.domain.entities.exports import DestinationExport, ExportDay, ModeExport, TransitShipment


class ExportSource(ABC):
    @abstractmethod
    def for_companies(self, companies: tuple[str, ...]) -> "ExportSource": ...

    @abstractmethod
    def day_summaries(self, start: date, end: date) -> list[ExportDay]: ...

    @abstractmethod
    def destination_summaries(self, start: date, end: date) -> list[DestinationExport]: ...

    @abstractmethod
    def mode_summaries(self, start: date, end: date) -> list[ModeExport]: ...

    @abstractmethod
    def in_transit(self, top: int) -> list[TransitShipment]: ...
