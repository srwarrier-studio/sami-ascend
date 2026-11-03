from abc import ABC, abstractmethod

from butterfly.domain.entities.finance import CashPayment


class FinanceRepo(ABC):
    @abstractmethod
    def payments(self) -> list[CashPayment]: ...

    def listing(self, entity: str):
        return getattr(self, entity)()

    def summary_listing(self, name: str):
        return None
