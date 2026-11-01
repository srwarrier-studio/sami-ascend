from abc import ABC, abstractmethod
from datetime import date

from synapse_api.domain.entities.catalog import CatalogEntry


class WidgetCatalog(ABC):
    @abstractmethod
    def for_companies(self, companies: tuple[str, ...]) -> "WidgetCatalog": ...

    @abstractmethod
    def entries(self) -> list[CatalogEntry]: ...

    @abstractmethod
    def data(self, entry_id: str, today: date, currency: str) -> dict: ...
