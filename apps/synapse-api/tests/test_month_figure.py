from datetime import date
from decimal import Decimal

import pytest

from synapse_api.application.month_figure import GetMonthFigure
from synapse_api.domain.entities.sales import DailySales
from synapse_api.domain.errors import InvalidQuery
from synapse_api.infrastructure.mock_sales_source import MockSalesSource

TODAY = date(2026, 10, 31)


def day(d: date, amount: str, orders: int = 1, currency: str = "INR") -> DailySales:
    return DailySales(d, Decimal(amount), orders, currency)


SOURCE = MockSalesSource(
    daily=[
        day(date(2026, 6, 5), "100.00"),
        day(date(2026, 7, 5), "200.00"),
        day(date(2026, 8, 3), "120.00", 2),
        day(date(2026, 8, 20), "80.00", 3),
    ]
)


def figure(month="2026-08", trend=6, today=TODAY, source=SOURCE):
    return GetMonthFigure(source).execute(today, month, trend)


class TestFigure:
    def test_amount_and_order_count_of_the_month(self):
        [result] = figure()
        assert (result.net_amount, result.order_count) == (Decimal("200.00"), 5)

    def test_change_against_the_month_before(self):
        [result] = figure()
        assert result.previous_change_percent == Decimal("0.00")
        [july] = figure("2026-07")
        assert july.previous_change_percent == Decimal("100.00")

    def test_change_is_null_when_the_month_before_has_no_sales(self):
        [result] = figure("2026-06")
        assert result.previous_change_percent is None


class TestTrend:
    def test_months_come_oldest_first_and_end_with_the_month(self):
        [result] = figure(trend=3)
        assert [(t.month, t.net_amount) for t in result.trend] == [(6, Decimal("100.00")), (7, Decimal("200.00")), (8, Decimal("200.00"))]

    def test_it_crosses_a_year_boundary(self):
        [result] = figure("2026-02", trend=3, source=MockSalesSource(daily=[day(date(2025, 12, 5), "9.00")]))
        assert [(t.year, t.month) for t in result.trend] == [(2025, 12), (2026, 1), (2026, 2)]

    def test_default_is_six_months(self):
        [result] = GetMonthFigure(SOURCE).execute(TODAY, "2026-08")
        assert len(result.trend) == 6


class TestComplete:
    def test_a_finished_month_is_complete(self):
        assert figure()[0].complete is True

    def test_the_current_month_is_not_complete_until_it_is_over(self):
        source = MockSalesSource(daily=[day(date(2026, 10, 5), "5.00")])
        assert figure("2026-10", today=date(2026, 10, 30), source=source)[0].complete is False
        assert figure("2026-10", today=date(2026, 11, 1), source=source)[0].complete is True


class TestNoData:
    def test_a_window_without_rows_gives_an_empty_list(self):
        assert figure(source=MockSalesSource()) == []


class TestInvalid:
    @pytest.mark.parametrize("month,trend", [("2026-11", 6), ("2026-8", 6), ("august", 6), ("2026-13", 6), ("2026-08", 0), ("2026-08", 25)])
    def test_each_rule(self, month, trend):
        with pytest.raises(InvalidQuery):
            figure(month, trend)

    def test_the_current_month_is_allowed(self):
        figure("2026-10")
