from butterfly.domain.entities.finance import CashPayment
from butterfly.domain.repositories.finance_repo import FinanceRepo


class InMemoryFinanceRepo(FinanceRepo):
    def __init__(self, payments: list[CashPayment] | None = None):
        self._payments = payments or []

    def payments(self) -> list[CashPayment]:
        return list(self._payments)
