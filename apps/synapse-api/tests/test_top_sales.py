from datetime import date
from decimal import Decimal

import pytest

from synapse_api.application.top_sales import GetTopCustomers, GetTopMaterials
from synapse_api.domain.entities.sales import CustomerSales, MaterialSales
from synapse_api.domain.errors import InvalidQuery
from synapse_api.infrastructure.mock_sales_source import MockSalesSource

TODAY = date(2026, 10, 27)


def customer(code: str, d: date, amount: str, count: int = 1, currency: str = "INR") -> CustomerSales:
    return CustomerSales(code, f"Name {code}", d, Decimal(amount), count, currency)


def material(code: str, d: date, quantity: str, amount: str, currency: str = "INR") -> MaterialSales:
    return MaterialSales(code, f"Desc {code}", d, Decimal(quantity), "EA", Decimal(amount), currency)


class RecordingSource(MockSalesSource):
    calls = 0

    def customer_sales(self, start, end):
        self.calls += 1
        return super().customer_sales(start, end)

    def material_sales(self, start, end):
        self.calls += 1
        return super().material_sales(start, end)


class TestGetTopCustomers:
    def test_sums_days_and_ranks_descending(self):
        source = MockSalesSource(
            customers=[
                customer("A", date(2026, 10, 1), "10", 1),
                customer("A", date(2026, 10, 2), "10", 2),
                customer("B", date(2026, 10, 3), "50", 1),
            ]
        )
        result = GetTopCustomers(source).execute(TODAY)
        assert [(c.customer, c.net_amount, c.order_count) for c in result] == [
            ("B", Decimal("50"), 1),
            ("A", Decimal("20"), 3),
        ]

    def test_only_this_month_counts(self):
        source = MockSalesSource(customers=[customer("A", date(2026, 9, 30), "999"), customer("B", date(2026, 10, 1), "1")])
        assert [c.customer for c in GetTopCustomers(source).execute(TODAY)] == ["B"]

    def test_cuts_to_top(self):
        source = MockSalesSource(customers=[customer(c, date(2026, 10, 1), a) for c, a in [("A", "1"), ("B", "3"), ("C", "2")]])
        assert [c.customer for c in GetTopCustomers(source).execute(TODAY, top=2)] == ["B", "C"]

    def test_ties_are_ordered_by_customer_code(self):
        source = MockSalesSource(customers=[customer(c, date(2026, 10, 1), "5") for c in ["C", "A", "B"]])
        assert [c.customer for c in GetTopCustomers(source).execute(TODAY)] == ["A", "B", "C"]

    def test_currencies_are_ranked_separately(self):
        source = MockSalesSource(
            customers=[
                customer("A", date(2026, 10, 1), "1"),
                customer("B", date(2026, 10, 1), "2"),
                customer("A", date(2026, 10, 1), "900", currency="USD"),
            ]
        )
        result = GetTopCustomers(source).execute(TODAY, top=1)
        assert [(c.currency, c.customer) for c in result] == [("INR", "B"), ("USD", "A")]

    @pytest.mark.parametrize("top", [0, 51])
    def test_top_out_of_range_does_not_call_source(self, top):
        source = RecordingSource()
        with pytest.raises(InvalidQuery):
            GetTopCustomers(source).execute(TODAY, top=top)
        assert source.calls == 0


class TestGetTopMaterials:
    def test_sums_quantity_and_amount_and_ranks_descending(self):
        source = MockSalesSource(
            materials=[
                material("M1", date(2026, 10, 1), "2", "10"),
                material("M1", date(2026, 10, 2), "3", "15"),
                material("M2", date(2026, 10, 3), "1", "100"),
            ]
        )
        result = GetTopMaterials(source).execute(TODAY)
        assert [(m.material, m.quantity, m.net_amount, m.unit, m.description) for m in result] == [
            ("M2", Decimal("1"), Decimal("100"), "EA", "Desc M2"),
            ("M1", Decimal("5"), Decimal("25"), "EA", "Desc M1"),
        ]

    def test_only_this_month_counts(self):
        source = MockSalesSource(materials=[material("M1", date(2026, 9, 30), "1", "999")])
        assert GetTopMaterials(source).execute(TODAY) == []

    def test_cuts_to_top_and_breaks_ties_by_code(self):
        source = MockSalesSource(materials=[material(m, date(2026, 10, 1), "1", "5") for m in ["M3", "M1", "M2"]])
        assert [m.material for m in GetTopMaterials(source).execute(TODAY, top=2)] == ["M1", "M2"]

    def test_currencies_are_ranked_separately(self):
        source = MockSalesSource(
            materials=[
                material("M1", date(2026, 10, 1), "1", "1"),
                material("M2", date(2026, 10, 1), "1", "2"),
                material("M1", date(2026, 10, 1), "1", "9", "USD"),
            ]
        )
        result = GetTopMaterials(source).execute(TODAY, top=1)
        assert [(m.currency, m.material) for m in result] == [("INR", "M2"), ("USD", "M1")]

    @pytest.mark.parametrize("top", [0, 51])
    def test_top_out_of_range_does_not_call_source(self, top):
        source = RecordingSource()
        with pytest.raises(InvalidQuery):
            GetTopMaterials(source).execute(TODAY, top=top)
        assert source.calls == 0
