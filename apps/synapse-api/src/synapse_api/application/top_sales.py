from datetime import date
from decimal import Decimal

from synapse_api.domain.entities.kpis import RankedCustomer, RankedMaterial
from synapse_api.domain.errors import InvalidQuery
from synapse_api.domain.gateways.sales_source import SalesSource


def check_top(top: int) -> None:
    if not 1 <= top <= 50:
        raise InvalidQuery()


def keep_top_per_currency(ranked: list, top: int, code) -> list:
    ranked.sort(key=lambda r: (r.currency, -r.net_amount, code(r)))
    kept = []
    seen: dict[str, int] = {}
    for r in ranked:
        seen[r.currency] = seen.get(r.currency, 0) + 1
        if seen[r.currency] <= top:
            kept.append(r)
    return kept


class GetTopCustomers:
    def __init__(self, source: SalesSource):
        self.source = source

    def execute(self, today: date, top: int = 5) -> list[RankedCustomer]:
        check_top(top)
        sums: dict[tuple[str, str], RankedCustomer] = {}
        for row in self.source.customer_sales(today.replace(day=1), today):
            key = (row.customer, row.currency)
            old = sums.get(key)
            sums[key] = RankedCustomer(
                row.customer,
                row.name,
                row.net_amount + (old.net_amount if old else Decimal(0)),
                row.order_count + (old.order_count if old else 0),
                row.currency,
            )
        return keep_top_per_currency(list(sums.values()), top, lambda r: r.customer)


class GetTopMaterials:
    def __init__(self, source: SalesSource):
        self.source = source

    def execute(self, today: date, top: int = 5) -> list[RankedMaterial]:
        check_top(top)
        sums: dict[tuple[str, str], RankedMaterial] = {}
        for row in self.source.material_sales(today.replace(day=1), today):
            key = (row.material, row.currency)
            old = sums.get(key)
            sums[key] = RankedMaterial(
                row.material,
                old.description if old else row.description,
                row.quantity + (old.quantity if old else Decimal(0)),
                old.unit if old else row.unit,
                row.net_amount + (old.net_amount if old else Decimal(0)),
                row.currency,
            )
        return keep_top_per_currency(list(sums.values()), top, lambda r: r.material)
