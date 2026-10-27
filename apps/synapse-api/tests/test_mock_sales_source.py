from datetime import date
from decimal import Decimal

import pytest

from synapse_api.domain.entities.sales import DailySales, HighValueOrder
from synapse_api.domain.errors import SapUnavailable
from synapse_api.infrastructure.mock_sales_source import MockSalesSource


def day(d: int) -> DailySales:
    return DailySales(date(2026, 10, d), Decimal("100.00"), 1, "INR")


def order(number: str, d: int, amount: str, status: str = "A") -> HighValueOrder:
    return HighValueOrder(number, "Acme", date(2026, 10, d), Decimal(amount), "INR", status)


class TestDateRange:
    def test_drops_rows_outside_range(self):
        source = MockSalesSource(daily=[day(1), day(5), day(9)])
        assert source.daily_sales(date(2026, 10, 2), date(2026, 10, 8)) == [day(5)]

    def test_range_is_inclusive_and_ordered_by_date(self):
        source = MockSalesSource(daily=[day(5), day(1), day(3)])
        assert source.daily_sales(date(2026, 10, 1), date(2026, 10, 5)) == [day(1), day(3), day(5)]


class TestHighValueOrders:
    def test_excludes_cancelled_and_small_newest_first_limited(self):
        source = MockSalesSource(orders=[
            order("1", 1, "900"), order("2", 3, "900"), order("3", 4, "900", "X"),
            order("4", 5, "10"), order("5", 2, "900"),
        ])
        assert [o.order for o in source.high_value_orders(Decimal("500"), 2)] == ["2", "5"]


class TestFailure:
    def test_raises_sap_unavailable(self):
        source = MockSalesSource()
        source.fail()
        with pytest.raises(SapUnavailable):
            source.daily_sales(date(2026, 10, 1), date(2026, 10, 2))
        with pytest.raises(SapUnavailable):
            source.high_value_orders(Decimal("1"), 1)
