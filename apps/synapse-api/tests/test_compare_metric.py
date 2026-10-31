from datetime import date
from decimal import Decimal

import pytest

from synapse_api.application.compare_metric import CompareMetric
from synapse_api.domain.entities.metric_row import MetricRow
from synapse_api.domain.errors import InvalidQuery, MetricNotFound
from synapse_api.infrastructure.mock_metric_source import MockMetricSource
from synapse_api.infrastructure.registry_loader import load_registry
from synapse_api.infrastructure.settings import REGISTRY_PATH

REGISTRY = load_registry(REGISTRY_PATH)

JULY = (date(2026, 7, 1), date(2026, 7, 31))
AUGUST = (date(2026, 8, 1), date(2026, 8, 31))


def customer(code: str, d: date, amount: str, currency: str = "INR") -> MetricRow:
    return MetricRow(code, f"Name {code}", d, Decimal(amount), currency, count=1)


def material(code: str, d: date, quantity: str, amount: str, currency: str = "INR") -> MetricRow:
    return MetricRow(code, f"Desc {code}", d, Decimal(amount), currency, Decimal(quantity), "EA")


def day_row(d: date, amount: str, orders: int, currency: str = "INR") -> MetricRow:
    return MetricRow(None, "", d, Decimal(amount), currency, count=orders)


def MockSalesSource(daily=None, customers=None, materials=None) -> MockMetricSource:
    return MockMetricSource({("sales", "day"): daily or [], ("sales", "customer"): customers or [], ("sales", "material"): materials or []})


def compare(source, by=None, top=10, current=AUGUST, previous=JULY, metric="sales"):
    return CompareMetric(source, REGISTRY).execute(metric, *current, *previous, by, top)


JULY_DAY, AUGUST_DAY = date(2026, 7, 10), date(2026, 8, 10)


class TestTotals:
    def test_without_a_dimension_only_totals_come_back(self):
        source = MockSalesSource(daily=[day_row(JULY_DAY, "200.00", 2), day_row(AUGUST_DAY, "170.00", 1, "INR")])
        [result] = compare(source)
        assert (result.current, result.previous, result.change, result.change_percent) == (Decimal("170.00"), Decimal("200.00"), Decimal("-30.00"), Decimal("-15.00"))
        assert result.rows is None

    def test_percent_is_null_when_the_earlier_period_is_empty(self):
        [result] = compare(MockSalesSource(daily=[day_row(AUGUST_DAY, "50.00", 1, "INR")]))
        assert result.change_percent is None

    def test_periods_may_differ_in_length(self):
        source = MockSalesSource(daily=[day_row(date(2026, 8, 3), "10.00", 1), day_row(date(2026, 7, 3), "4.00", 1)])
        [result] = compare(source, current=(date(2026, 8, 1), date(2026, 8, 7)), previous=(date(2026, 7, 1), date(2026, 7, 31)))
        assert result.change == Decimal("6.00")

    def test_two_currencies_are_two_results(self):
        source = MockSalesSource(daily=[day_row(AUGUST_DAY, "5.00", 1, "EUR"), day_row(AUGUST_DAY, "7.00", 1, "INR")])
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


class TestMetrics:
    def test_an_unknown_metric_is_not_found(self):
        with pytest.raises(MetricNotFound):
            compare(MockMetricSource(), metric="weather")

    def test_the_day_dimension_is_not_a_split(self):
        with pytest.raises(InvalidQuery):
            compare(MockMetricSource(), by="day")

    def test_a_dimension_the_metric_does_not_have_is_invalid(self):
        with pytest.raises(InvalidQuery):
            compare(MockMetricSource(), by="supplier")


class TestAnotherMetricNeedsNoCode:
    def test_a_registered_purchases_metric_compares_by_supplier_and_material(self, tmp_path):
        path = tmp_path / "r.toml"
        path.write_text(
            """
[metric.purchases]
label = "Purchases"
service = "drivers"
measure = "TotalNetAmount"
date = "OrderDate"
currency = "Currency"
by.day = { entity = "PurchaseSummaryByDay", order = "OrderDate" }
by.supplier = { entity = "PurchaseSummaryBySupplier", key = "Supplier", name = "SupplierName", order = "OrderDate" }
by.material = { entity = "PurchaseSummaryByMaterial", key = "Material", name = "MaterialDescription", unit = "QuantityUnit", quantity = "TotalQuantity", order = "OrderDate" }
"""
        )
        source = MockMetricSource({
            ("purchases", "supplier"): [customer("S1", JULY_DAY, "100.00"), customer("S1", AUGUST_DAY, "120.00")],
            ("purchases", "material"): [material("RAW-1", JULY_DAY, "10.000", "100.00"), material("RAW-1", AUGUST_DAY, "10.000", "120.00")],
        })
        registry = load_registry(path)
        [by_supplier] = CompareMetric(source, registry).execute("purchases", *AUGUST, *JULY, "supplier")
        [by_material] = CompareMetric(source, registry).execute("purchases", *AUGUST, *JULY, "material")
        assert by_supplier.rows[0].change == Decimal("20.00") and by_supplier.rows[0].price_effect is None
        assert (by_material.rows[0].price_effect, by_material.rows[0].volume_effect) == (Decimal("20.00"), Decimal("0.00"))


class TestSapDown:
    def test_a_failing_source_raises_and_returns_nothing(self):
        from synapse_api.domain.errors import SapUnavailable

        source = MockSalesSource()
        source.fail()
        with pytest.raises(SapUnavailable):
            compare(source, "customer")
