from datetime import date
from decimal import Decimal

import pytest

from synapse_api.application.period_sales import GetMonthToDateSales, GetTodaySales, GetYearToDateSales
from synapse_api.domain.entities.sales import DailySales
from synapse_api.domain.errors import SapUnavailable
from synapse_api.infrastructure.mock_sales_source import MockSalesSource

TODAY = date(2026, 10, 27)


def sales(d: date, amount: str, count: int = 1, currency: str = "INR") -> DailySales:
    return DailySales(d, Decimal(amount), count, currency)


SOURCE = MockSalesSource(
    daily=[
        sales(date(2025, 12, 31), "1000"),
        sales(date(2026, 1, 1), "10", 1),
        sales(date(2026, 9, 30), "20", 2),
        sales(date(2026, 10, 1), "30", 3),
        sales(date(2026, 10, 27), "40", 4),
        sales(date(2026, 10, 27), "5", 1, "USD"),
        sales(date(2026, 10, 28), "5000"),
    ]
)


class TestGetTodaySales:
    def test_counts_only_today_per_currency(self):
        totals = GetTodaySales(SOURCE).execute(TODAY)
        assert [(t.currency, t.net_amount, t.order_count) for t in totals] == [
            ("INR", Decimal("40"), 4),
            ("USD", Decimal("5"), 1),
        ]

    def test_period_is_today(self):
        total = GetTodaySales(SOURCE).execute(TODAY)[0]
        assert (total.start, total.end) == (TODAY, TODAY)

    def test_no_sales_gives_empty_list(self):
        assert GetTodaySales(MockSalesSource()).execute(TODAY) == []


class TestGetMonthToDateSales:
    def test_includes_first_of_month_and_today_only(self):
        totals = GetMonthToDateSales(SOURCE).execute(TODAY)
        assert [(t.currency, t.net_amount, t.order_count) for t in totals] == [
            ("INR", Decimal("70"), 7),
            ("USD", Decimal("5"), 1),
        ]

    def test_period_starts_on_first(self):
        assert GetMonthToDateSales(SOURCE).execute(TODAY)[0].start == date(2026, 10, 1)


class TestGetYearToDateSales:
    def test_includes_first_of_january_and_excludes_last_year(self):
        totals = GetYearToDateSales(SOURCE).execute(TODAY)
        assert [(t.currency, t.net_amount, t.order_count) for t in totals] == [
            ("INR", Decimal("100"), 10),
            ("USD", Decimal("5"), 1),
        ]

    def test_period_starts_on_first_of_january(self):
        assert GetYearToDateSales(SOURCE).execute(TODAY)[0].start == date(2026, 1, 1)


class TestSourceFailure:
    def test_sap_unavailable_propagates(self):
        source = MockSalesSource()
        source.fail()
        with pytest.raises(SapUnavailable):
            GetTodaySales(source).execute(TODAY)
