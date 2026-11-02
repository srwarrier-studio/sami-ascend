from abc import ABC, abstractmethod
from datetime import date

from synapse_api.domain.entities.registry import RecordType


class RecordSource(ABC):
    @abstractmethod
    def for_companies(self, companies: tuple[str, ...]) -> "RecordSource": ...

    @abstractmethod
    def rows(self, record: RecordType, key_field: str, key: str, end: date | None) -> list[dict]: ...
