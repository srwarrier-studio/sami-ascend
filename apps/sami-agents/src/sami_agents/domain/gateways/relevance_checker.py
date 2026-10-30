from abc import ABC, abstractmethod

from sami_agents.domain.entities.catalog import CatalogEntry


class RelevanceChecker(ABC):
    @abstractmethod
    def check(self, message: str, entry: CatalogEntry) -> float: ...
