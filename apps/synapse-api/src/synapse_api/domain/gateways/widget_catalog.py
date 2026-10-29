from abc import ABC, abstractmethod
from datetime import date

from synapse_api.domain.entities.catalog import CatalogEntry


class WidgetCatalog(ABC):
    @abstractmethod
    def entries(self) -> list[CatalogEntry]: ...

    @abstractmethod
    def data(self, entry_id: str, today: date) -> dict: ...
