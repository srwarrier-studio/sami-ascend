from abc import ABC, abstractmethod

from sami_agents.domain.entities.catalog import CatalogEntry


class ChatModel(ABC):
    @abstractmethod
    def pick_widgets(self, message: str, catalog: list[CatalogEntry]) -> list[str]: ...
