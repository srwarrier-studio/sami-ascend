from butterfly.domain.entities.inventory import MaterialStock, StockMovement, StockValueMonth
from butterfly.domain.repositories.inventory_repo import InventoryRepo


class InMemoryInventoryRepo(InventoryRepo):
    def __init__(self, stocks: list[MaterialStock] | None = None, movements: list[StockMovement] | None = None, monthly: list[StockValueMonth] | None = None):
        self._stocks = stocks or []
        self._movements = movements or []
        self._monthly = monthly or []

    def stocks(self) -> list[MaterialStock]:
        return list(self._stocks)

    def movements(self) -> list[StockMovement]:
        return list(self._movements)

    def monthly_values(self) -> list[StockValueMonth]:
        return list(self._monthly)
