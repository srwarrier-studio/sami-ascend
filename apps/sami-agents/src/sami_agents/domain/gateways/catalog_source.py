from abc import ABC, abstractmethod

from sami_agents.domain.entities.catalog import CatalogEntry


class CatalogSource(ABC):
    @abstractmethod
    def entries(self, access_token: str) -> list[CatalogEntry]: ...
