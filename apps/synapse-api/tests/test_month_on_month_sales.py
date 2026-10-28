from datetime import date
from decimal import Decimal

import pytest

from synapse_api.application.month_on_month_sales import GetMonthOnMonthSales
from synapse_api.domain.entities.sales import DailySales
from synapse_api.domain.errors import InvalidQuery
from synapse_api.infrastructure.mock_sales_source import MockSalesSource


def sales(d: date, amount: str, currency: str = "INR") -> DailySales:
    return DailySales(d, Decimal(amount), 1, currency)


class RecordingSource(MockSalesSource):
    calls = 0

    def daily_sales(self, start, end):
        self.calls += 1
        return super().daily_sales(start, end)


class TestGetMonthOnMonthSales:
    def test_sums_days_into_months_oldest_first(self):
        source = MockSalesSource(
            daily=[sales(date(2026, 9, 1), "10"), sales(date(2026, 9, 30), "5"), sales(date(2026, 10, 3), "7")]
        )
        result = GetMonthOnMonthSales(source).execute(date(2026, 10, 27), months=2)
        assert [(m.year, m.month, m.net_amount) for m in result] == [
            (2026, 9, Decimal("15")),
            (2026, 10, Decimal("7")),
        ]

    def test_month_without_sales_is_zero(self):
        source = MockSalesSource(daily=[sales(date(2026, 8, 5), "10")])
        result = GetMonthOnMonthSales(source).execute(date(2026, 10, 27), months=3)
        assert [m.net_amount for m in result] == [Decimal("10"), Decimal("0"), Decimal("0")]

    def test_january_looks_back_to_december(self):
        source = MockSalesSource(daily=[sales(date(2025, 12, 31), "4"), sales(date(2025, 11, 30), "9")])
        result = GetMonthOnMonthSales(source).execute(date(2026, 1, 15), months=2)
        assert [(m.year, m.month, m.net_amount) for m in result] == [
            (2025, 12, Decimal("4")),
            (2026, 1, Decimal("0")),
        ]

    def test_default_is_twelve_months_ending_this_month(self):
        source = MockSalesSource(daily=[sales(date(2025, 11, 1), "1")])
        result = GetMonthOnMonthSales(source).execute(date(2026, 10, 27))
        assert len(result) == 12
        assert (result[0].year, result[0].month) == (2025, 11)
        assert (result[-1].year, result[-1].month) == (2026, 10)

    def test_each_currency_gets_every_month(self):
        source = MockSalesSource(daily=[sales(date(2026, 10, 1), "1"), sales(date(2026, 9, 1), "2", "USD")])
        result = GetMonthOnMonthSales(source).execute(date(2026, 10, 27), months=2)
        assert [(m.currency, m.month, m.net_amount) for m in result] == [
            ("INR", 9, Decimal("0")),
            ("USD", 9, Decimal("2")),
            ("INR", 10, Decimal("1")),
            ("USD", 10, Decimal("0")),
        ]

    def test_no_sales_gives_empty_list(self):
        assert GetMonthOnMonthSales(MockSalesSource()).execute(date(2026, 10, 27)) == []

    @pytest.mark.parametrize("months", [0, -1, 25])
    def test_months_out_of_range_does_not_call_source(self, months):
        source = RecordingSource()
        with pytest.raises(InvalidQuery):
            GetMonthOnMonthSales(source).execute(date(2026, 10, 27), months=months)
        assert source.calls == 0
