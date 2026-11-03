from decimal import Decimal

from butterfly.domain.entities.inventory import (
    StockMovementSummaryByDay,
    StockMovementSummaryByHour,
    StockSummaryByMaterialGroup,
    StockSummaryByStatus,
    StockSummaryByWarehouse,
    StockValueMonth,
)
from butterfly.domain.repositories.inventory_repo import InventoryRepo

FLOW_TYPES = ("101", "131", "261", "601")


class SummarizeInventory:
    def __init__(self, repo: InventoryRepo):
        self.repo = repo

    def by_warehouse(self) -> list[StockSummaryByWarehouse]:
        totals: dict[tuple, list] = {}
        for stock in self.repo.stocks():
            entry = totals.setdefault((stock.plant, stock.storage_location, stock.currency, stock.company_code), [stock.storage_location_name, Decimal("0.00"), 0])
            entry[1] += stock.stock_value
            entry[2] += 1
        return [StockSummaryByWarehouse(plant, location, name, value, count, currency, company) for (plant, location, currency, company), (name, value, count) in sorted(totals.items())]

    def by_material_group(self) -> list[StockSummaryByMaterialGroup]:
        totals: dict[tuple, list] = {}
        for stock in self.repo.stocks():
            entry = totals.setdefault((stock.material_group, stock.currency, stock.company_code), [stock.material_group_name, Decimal("0.00"), 0])
            entry[1] += stock.stock_value
            entry[2] += 1
        return [StockSummaryByMaterialGroup(group, name, value, count, currency, company) for (group, currency, company), (name, value, count) in sorted(totals.items())]

    def by_status(self) -> list[StockSummaryByStatus]:
        totals: dict[tuple, list] = {}
        for stock in self.repo.stocks():
            entry = totals.setdefault((stock.stock_status, stock.currency, stock.company_code), [Decimal("0.00"), 0])
            entry[0] += stock.stock_value
            entry[1] += 1
        return [StockSummaryByStatus(status, value, count, currency, company) for (status, currency, company), (value, count) in sorted(totals.items())]

    def value_by_month(self) -> list[StockValueMonth]:
        return sorted(self.repo.monthly_values(), key=lambda v: (v.posting_period, v.currency, v.company_code))

    def movements_by_day(self) -> list[StockMovementSummaryByDay]:
        totals: dict[tuple, list] = {}
        for movement in self.repo.movements():
            if movement.movement_type not in FLOW_TYPES:
                continue
            entry = totals.setdefault((movement.posting_date, movement.currency, movement.company_code), [Decimal("0.00"), Decimal("0.00"), 0])
            entry[0 if movement.debit_credit_code == "S" else 1] += movement.amount
            entry[2] += 1
        return [StockMovementSummaryByDay(day, receipts, issues, count, currency, company) for (day, currency, company), (receipts, issues, count) in sorted(totals.items())]

    def movements_by_hour(self) -> list[StockMovementSummaryByHour]:
        totals: dict[tuple, int] = {}
        for movement in self.repo.movements():
            if movement.movement_type in FLOW_TYPES:
                key = (movement.posting_date, movement.entry_date_time.hour, movement.company_code)
                totals[key] = totals.get(key, 0) + 1
        return [StockMovementSummaryByHour(day, hour, count, company) for (day, hour, company), count in sorted(totals.items())]
