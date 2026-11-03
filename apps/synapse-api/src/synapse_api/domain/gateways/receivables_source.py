from abc import ABC, abstractmethod
from datetime import date

from synapse_api.domain.entities.receivables import AgeBucket, CustomerReceivable, ReceivablesTotal


class ReceivablesSource(ABC):
    @abstractmethod
    def for_companies(self, companies: tuple[str, ...]) -> "ReceivablesSource": ...

    @abstractmethod
    def totals(self, as_of: date) -> list[ReceivablesTotal]: ...

    @abstractmethod
    def by_customer(self, as_of: date) -> list[CustomerReceivable]: ...

    @abstractmethod
    def ageing(self, as_of: date) -> list[AgeBucket]: ...
