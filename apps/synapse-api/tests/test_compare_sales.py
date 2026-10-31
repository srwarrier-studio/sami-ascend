from datetime import date
from decimal import Decimal

import pytest

from synapse_api.application.compare_sales import CompareSales
from synapse_api.domain.entities.sales import CustomerSales, DailySales, MaterialSales
from synapse_api.domain.errors import InvalidQuery
from synapse_api.infrastructure.mock_sales_source import MockSalesSource

JULY = (date(2026, 7, 1), date(2026, 7, 31))
AUGUST = (date(2026, 8, 1), date(2026, 8, 31))


def customer(code: str, d: date, amount: str, currency: str = "INR") -> CustomerSales:
    return CustomerSales(code, f"Name {code}", d, Decimal(amount), 1, currency)


def material(code: str, d: date, quantity: str, amount: str, currency: str = "INR") -> MaterialSales:
    return MaterialSales(code, f"Desc {code}", d, Decimal(quantity), "EA", Decimal(amount), currency)


def compare(source, by=None, top=10, current=AUGUST, previous=JULY):
    return CompareSales(source).execute(*current, *previous, by, top)


JULY_DAY, AUGUST_DAY = date(2026, 7, 10), date(2026, 8, 10)


class TestTotals:
    def test_without_a_dimension_only_totals_come_back(self):
        source = MockSalesSource(daily=[DailySales(JULY_DAY, Decimal("200.00"), 2, "INR"), DailySales(AUGUST_DAY, Decimal("170.00"), 1, "INR")])
        [result] = compare(source)
        assert (result.current, result.previous, result.change, result.change_percent) == (Decimal("170.00"), Decimal("200.00"), Decimal("-30.00"), Decimal("-15.00"))
        assert result.rows is None

    def test_percent_is_null_when_the_earlier_period_is_empty(self):
        [result] = compare(MockSalesSource(daily=[DailySales(AUGUST_DAY, Decimal("50.00"), 1, "INR")]))
        assert result.change_percent is None

    def test_periods_may_differ_in_length(self):
        source = MockSalesSource(daily=[DailySales(date(2026, 8, 3), Decimal("10.00"), 1, "INR"), DailySales(date(2026, 7, 3), Decimal("4.00"), 1, "INR")])
        [result] = compare(source, current=(date(2026, 8, 1), date(2026, 8, 7)), previous=(date(2026, 7, 1), date(2026, 7, 31)))
        assert result.change == Decimal("6.00")

    def test_two_currencies_are_two_results(self):
        source = MockSalesSource(daily=[DailySales(AUGUST_DAY, Decimal("5.00"), 1, "EUR"), DailySales(AUGUST_DAY, Decimal("7.00"), 1, "INR")])
        assert [r.currency for r in compare(source)] == ["EUR", "INR"]


class TestByCustomer:
    SOURCE = MockSalesSource(
        customers=[
            customer("A", JULY_DAY, "100.00"), customer("A", AUGUST_DAY, "10.00"),
            customer("B", JULY_DAY, "50.00"), customer("B", AUGUST_DAY, "55.00"),
            customer("C", JULY_DAY, "20.00"), customer("C", AUGUST_DAY, "15.00"),
            customer("N", AUGUST_DAY, "8.00"),
        ]
    )

    def test_rows_are_ordered_by_the_size_of_the_change(self):
        [result] = compare(self.SOURCE, "customer")
        assert [r.key for r in result.rows] == ["A", "N", "B", "C"]

    def test_a_row_shows_both_periods_the_change_and_its_share(self):
        [result] = compare(self.SOURCE, "customer")
        a = result.rows[0]
        assert (a.name, a.current, a.previous, a.change) == ("Name A", Decimal("10.00"), Decimal("100.00"), Decimal("-90.00"))
        assert result.change == Decimal("-82.00")
        assert a.share_of_change_percent == Decimal("109.76")

    def test_a_customer_in_only_one_period_is_a_row_with_zero_for_the_other(self):
        [result] = compare(self.SOURCE, "customer")
        new = next(r for r in result.rows if r.key == "N")
        assert (new.previous, new.current) == (Decimal(0), Decimal("8.00"))
        lost = compare(self.SOURCE, "customer", current=(date(2026, 9, 1), date(2026, 9, 30)))[0].rows[0]
        assert lost.current == Decimal(0)

    def test_rows_with_other_add_up_to_the_total_change(self):
        [result] = compare(self.SOURCE, "customer", top=2)
        assert [r.key for r in result.rows] == ["A", "N", "other"]
        assert sum(r.change for r in result.rows) == result.change

    def test_there_is_no_other_row_when_nothing_is_left(self):
        [result] = compare(self.SOURCE, "customer", top=4)
        assert [r.key for r in result.rows] == ["A", "N", "B", "C"]

    def test_equal_changes_are_ordered_by_key(self):
        source = MockSalesSource(customers=[customer("Z", AUGUST_DAY, "5.00"), customer("Y", AUGUST_DAY, "5.00")])
        assert [r.key for r in compare(source, "customer")[0].rows] == ["Y", "Z"]

    def test_there_is_no_volume_or_price_split(self):
        row = compare(self.SOURCE, "customer")[0].rows[0]
        assert row.volume_effect is None and row.price_effect is None

    def test_share_is_null_when_the_total_change_is_zero(self):
        source = MockSalesSource(customers=[customer("A", JULY_DAY, "5.00"), customer("A", AUGUST_DAY, "5.00")])
        assert compare(source, "customer")[0].rows[0].share_of_change_percent is None


class TestByMaterial:
    def test_a_price_cut_shows_as_price_effect(self):
        source = MockSalesSource(materials=[material("M", JULY_DAY, "100.000", "1000.00"), material("M", AUGUST_DAY, "100.000", "850.00")])
        row = compare(source, "material")[0].rows[0]
        assert (row.price_previous, row.price_current) == (Decimal("10.0000"), Decimal("8.5000"))
        assert (row.volume_effect, row.price_effect) == (Decimal("0.00"), Decimal("-150.00"))

    def test_a_volume_change_shows_as_volume_effect(self):
        source = MockSalesSource(materials=[material("M", JULY_DAY, "100.000", "1000.00"), material("M", AUGUST_DAY, "80.000", "800.00")])
        row = compare(source, "material")[0].rows[0]
        assert (row.volume_effect, row.price_effect) == (Decimal("-200.00"), Decimal("0.00"))

    def test_the_two_effects_add_up_to_the_change(self):
        source = MockSalesSource(materials=[material("M", JULY_DAY, "30.000", "100.00"), material("M", AUGUST_DAY, "37.000", "151.00")])
        row = compare(source, "material")[0].rows[0]
        assert row.volume_effect + row.price_effect == row.change == Decimal("51.00")

    def test_a_material_never_sold_before_is_all_volume(self):
        row = compare(MockSalesSource(materials=[material("M", AUGUST_DAY, "10.000", "70.00")]), "material")[0].rows[0]
        assert (row.price_previous, row.volume_effect, row.price_effect) == (None, Decimal("70.00"), Decimal(0))

    def test_a_material_no_longer_sold_has_no_current_price(self):
        row = compare(MockSalesSource(materials=[material("M", JULY_DAY, "10.000", "70.00")]), "material")[0].rows[0]
        assert (row.price_current, row.quantity_current, row.change) == (None, Decimal(0), Decimal("-70.00"))

    def test_other_carries_the_effects_of_the_rest(self):
        source = MockSalesSource(materials=[
            material("A", JULY_DAY, "10.000", "100.00"), material("A", AUGUST_DAY, "10.000", "50.00"),
            material("B", JULY_DAY, "10.000", "100.00"), material("B", AUGUST_DAY, "12.000", "100.00"),
            material("C", JULY_DAY, "10.000", "100.00"), material("C", AUGUST_DAY, "10.000", "101.00"),
        ])
        [result] = compare(source, "material", top=1)
        other = result.rows[-1]
        assert other.key == "other"
        assert sum(r.volume_effect + r.price_effect for r in result.rows) == result.change
        assert other.volume_effect + other.price_effect == other.change


class TestInvalidQueries:
    SOURCE = MockSalesSource()

    @pytest.mark.parametrize(
        "current,previous,by,top",
        [
            ((date(2026, 8, 2), date(2026, 8, 1)), JULY, None, 10),
            (AUGUST, (date(2026, 7, 31), date(2026, 7, 1)), None, 10),
            ((date(2025, 1, 1), date(2026, 2, 5)), JULY, None, 10),
            (AUGUST, (date(2025, 1, 1), date(2026, 2, 5)), None, 10),
            (AUGUST, JULY, "region", 10),
            (AUGUST, JULY, "customer", 0),
            (AUGUST, JULY, "customer", 51),
        ],
    )
    def test_each_rule(self, current, previous, by, top):
        with pytest.raises(InvalidQuery):
            compare(self.SOURCE, by, top, current, previous)

    def test_exactly_400_days_is_allowed(self):
        compare(self.SOURCE, current=(date(2025, 1, 2), date(2026, 2, 5)))


class TestSapDown:
    def test_a_failing_source_raises_and_returns_nothing(self):
        from synapse_api.domain.errors import SapUnavailable

        source = MockSalesSource()
        source.fail()
        with pytest.raises(SapUnavailable):
            compare(source, "customer")
