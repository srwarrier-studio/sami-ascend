from abc import ABC, abstractmethod
from datetime import date

from synapse_api.domain.entities.finance import CashDay, ExpenseDay, IncomingPayment


class FinanceSource(ABC):
    @abstractmethod
    def for_companies(self, companies: tuple[str, ...]) -> "FinanceSource": ...

    @abstractmethod
    def cash_days(self, start: date, end: date) -> list[CashDay]: ...

    @abstractmethod
    def expense_days(self, start: date, end: date) -> list[ExpenseDay]: ...

    @abstractmethod
    def incoming_payments(self, top: int) -> list[IncomingPayment]: ...
