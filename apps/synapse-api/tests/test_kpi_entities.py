from datetime import date
from decimal import Decimal

import pytest

from synapse_api.domain.entities.kpis import MonthSales, RankedCustomer, RankedMaterial, SalesTotal
from synapse_api.domain.errors import InvalidQuery


class TestResultTypes:
    def test_sales_total(self):
        total = SalesTotal(date(2026, 10, 1), date(2026, 10, 27), Decimal("10.50"), 2, "INR")
        assert (total.net_amount, total.order_count, total.currency) == (Decimal("10.50"), 2, "INR")

    def test_ranked_customer(self):
        assert RankedCustomer("C1", "Acme", Decimal("5"), 1, "INR").name == "Acme"

    def test_ranked_material(self):
        assert RankedMaterial("M1", "Bolt", Decimal("3"), "EA", Decimal("9"), "INR").unit == "EA"

    def test_month_sales(self):
        assert MonthSales(2026, 10, Decimal("1"), "INR").month == 10

    def test_results_are_immutable(self):
        with pytest.raises(AttributeError):
            MonthSales(2026, 10, Decimal("1"), "INR").month = 11


class TestInvalidQuery:
    def test_is_an_exception(self):
        with pytest.raises(InvalidQuery):
            raise InvalidQuery()
