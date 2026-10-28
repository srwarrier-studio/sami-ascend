from decimal import Decimal

from synapse_api.domain.entities.sales import HighValueOrder
from synapse_api.domain.errors import InvalidQuery
from synapse_api.domain.gateways.sales_source import SalesSource


class GetRecentHighValueOrders:
    def __init__(self, source: SalesSource):
        self.source = source

    def execute(self, minimum: Decimal, top: int = 5) -> list[HighValueOrder]:
        if not 1 <= top <= 50:
            raise InvalidQuery()
        return self.source.high_value_orders(minimum, top)
