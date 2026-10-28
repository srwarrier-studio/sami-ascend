from datetime import date
from decimal import Decimal

import pytest

from synapse_api.application.recent_high_value_orders import GetRecentHighValueOrders
from synapse_api.domain.entities.sales import HighValueOrder
from synapse_api.domain.errors import InvalidQuery
from synapse_api.infrastructure.mock_sales_source import MockSalesSource


def order(number: str, d: int, amount: str) -> HighValueOrder:
    return HighValueOrder(number, "Acme", date(2026, 10, d), Decimal(amount), "INR", "A")


class RecordingSource(MockSalesSource):
    calls = 0

    def high_value_orders(self, minimum, top):
        self.calls += 1
        return super().high_value_orders(minimum, top)


class TestGetRecentHighValueOrders:
    def test_passes_minimum_and_top_to_source(self):
        source = MockSalesSource(orders=[order("1", 1, "50"), order("2", 2, "500"), order("3", 3, "600")])
        result = GetRecentHighValueOrders(source).execute(Decimal("100"), top=1)
        assert [o.order for o in result] == ["3"]

    def test_default_top_is_five(self):
        source = MockSalesSource(orders=[order(str(n), n, "500") for n in range(1, 9)])
        assert len(GetRecentHighValueOrders(source).execute(Decimal("100"))) == 5

    @pytest.mark.parametrize("top", [0, 51])
    def test_top_out_of_range_does_not_call_source(self, top):
        source = RecordingSource()
        with pytest.raises(InvalidQuery):
            GetRecentHighValueOrders(source).execute(Decimal("100"), top=top)
        assert source.calls == 0
