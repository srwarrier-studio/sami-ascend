import hashlib
from datetime import date
from decimal import Decimal

from butterfly.domain.entities.scenario import (
    Cancellations,
    ContractEnd,
    CustomerLoss,
    Drop,
    PriceChange,
    ProductionDelay,
    Scenario,
    SupplyDelay,
)
from butterfly.infrastructure.memory.story_seed import build_story_seed

TODAY = date(2026, 10, 31)
QUIET = build_story_seed(TODAY, Scenario("test", ()))
ACME = "0000100001"
EASTERN = "0000100005"


def seed_with(*events):
    return build_story_seed(TODAY, Scenario("test", events))


def digest(rows) -> str:
    return hashlib.sha256(repr(rows).encode()).hexdigest()[:16]


def fingerprints(day: date) -> dict:
    seed = build_story_seed(day)
    return {name: digest(getattr(seed, name)) for name in ("orders", "contracts", "production_orders", "components", "deliveries")}


def orders_of(seed, customer, start, end):
    return [o for o in seed.orders if o.sold_to_party == customer and start <= o.order_date <= end]


BUTTERFLY_EIGHT = {
    date(2026, 10, 31): {"orders": "7e38e283a5d06c4d", "contracts": "77208a2c8362559d", "production_orders": "918f6fc80d8cf23d", "components": "4ee79d2ae772c724"},
    date(2026, 8, 15): {"orders": "a02b9f4da62e019a", "contracts": "1f592dbcff450c37", "production_orders": "039f27b642636434", "components": "c57ee25e615e4775"},
    date(2026, 9, 1): {"orders": "d848cd472db06d5f", "contracts": "1f592dbcff450c37", "production_orders": "68b8b8dc219e118c", "components": "afac484cb3ddae0a"},
}
DELIVERIES_WITH_AMOUNTS = {date(2026, 10, 31): "0a3d86e25ebef67a", date(2026, 8, 15): "03790bf72890111e", date(2026, 9, 1): "0daa551b818585ac"}


class TestAugustContractStaysAsButterflyEight:
    def test_orders_contracts_production_and_components_are_identical_on_three_dates(self):
        for day, expected in BUTTERFLY_EIGHT.items():
            actual = fingerprints(day)
            assert {k: actual[k] for k in expected} == expected

    def test_deliveries_changed_only_by_the_amount_fields_and_are_pinned_again(self):
        for day, expected in DELIVERIES_WITH_AMOUNTS.items():
            assert fingerprints(day)["deliveries"] == expected

    def test_every_delivery_amount_is_the_ordered_quantity_times_the_price_of_its_raw_material(self):
        prices = {"RAW-2001": "46.00", "RAW-2002": "52.00", "RAW-2003": "610.00", "RAW-2004": "190.00", "RAW-2005": "70.00", "RAW-2006": "48.00"}
        for d in QUIET.deliveries:
            assert d.net_amount == d.ordered_quantity * Decimal(prices[d.material])
            assert d.transaction_currency == "INR"


class TestContractEnd:
    def test_orders_stop_until_renewal_and_contracts_are_cut_and_renewed(self):
        seed = seed_with(ContractEnd(4, date(2026, 8, 3), date(2026, 9, 1), "0040000999"))
        assert orders_of(seed, EASTERN, date(2026, 8, 4), date(2026, 8, 31)) == []
        assert orders_of(seed, EASTERN, date(2026, 9, 1), date(2026, 9, 30))
        eastern = [c for c in seed.contracts if c.sold_to_party == EASTERN]
        cut = next(c for c in eastern if c.valid_to == date(2026, 8, 3))
        renewed = next(c for c in eastern if c.sales_contract == "0040000999")
        assert renewed.predecessor_contract == cut.sales_contract
        assert renewed.valid_from == date(2026, 9, 1)
        assert renewed.valid_to == date(2027, 8, 31)

    def test_without_renewal_orders_stay_stopped_and_no_contract_follows(self):
        seed = seed_with(ContractEnd(4, date(2026, 8, 3)))
        assert orders_of(seed, EASTERN, date(2026, 8, 4), TODAY) == []
        assert max(c.valid_to for c in seed.contracts if c.sold_to_party == EASTERN) == date(2026, 8, 3)

    def test_spot_orders_keep_a_trickle_of_single_item_orders(self):
        seed = seed_with(ContractEnd(4, date(2026, 8, 3), date(2026, 9, 1), "0040000999", spot=True))
        spot = orders_of(seed, EASTERN, date(2026, 8, 4), date(2026, 8, 31))
        assert spot and all(len(o.items) == 1 for o in spot)


class TestSupplyDelay:
    def test_the_delivery_is_late_by_the_given_days(self):
        seed = seed_with(SupplyDelay("RAW-2001", date(2026, 6, 1), 9))
        delivery = next(d for d in seed.deliveries if d.material == "RAW-2001" and d.promised_delivery_date == date(2026, 6, 14))
        assert (delivery.actual_delivery_date - delivery.promised_delivery_date).days == 9

    def test_without_a_drop_orders_are_unchanged(self):
        assert seed_with(SupplyDelay("RAW-2001", date(2026, 6, 1), 9)).orders == QUIET.orders

    def test_a_drop_removes_the_share_of_the_products_items_in_its_window(self):
        drop = Drop("RM-1001", date(2026, 6, 15), date(2026, 6, 30), 1, 2)
        seed = seed_with(SupplyDelay("RAW-2001", date(2026, 6, 1), 9, drop))
        def count(s):
            return sum(1 for o in s.orders if date(2026, 6, 15) <= o.order_date <= date(2026, 6, 30) for i in o.items if i.material == "RM-1001")
        assert count(seed) < 0.7 * count(QUIET)


class TestProductionDelay:
    def test_the_production_order_ends_late_with_the_reason(self):
        seed = seed_with(ProductionDelay("RM-1006", date(2026, 6, 1), 8, "MACHINE_BREAKDOWN"))
        order = next(p for p in seed.production_orders if p.material == "RM-1006" and p.delay_reason)
        assert (order.actual_end_date - order.planned_end_date).days == 8
        assert order.delay_reason == "MACHINE_BREAKDOWN"

    def test_a_drop_limited_to_some_customers_leaves_the_others_alone(self):
        drop = Drop("RM-1005", date(2026, 7, 1), date(2026, 7, 31), 1, 2, (1,))
        seed = seed_with(ProductionDelay("RM-1005", date(2026, 7, 1), 10, "MACHINE_BREAKDOWN", drop))
        def bearings(s, customer):
            return sum(1 for o in s.orders if o.sold_to_party == customer and date(2026, 7, 1) <= o.order_date <= date(2026, 7, 31) for i in o.items if i.material == "RM-1005")
        assert bearings(seed, "0000100002") < bearings(QUIET, "0000100002")
        assert bearings(seed, "0000100003") == bearings(QUIET, "0000100003")


class TestPriceChange:
    def test_net_amounts_change_and_quantities_do_not(self):
        seed = seed_with(PriceChange("RM-1001", "0.85", date(2026, 8, 1)))
        after = [(a, b) for a, b in zip(QUIET.orders, seed.orders) if a.order_date >= date(2026, 8, 1)]
        for old, new in after:
            for old_item, new_item in zip(old.items, new.items):
                assert old_item.quantity == new_item.quantity
                if old_item.material == "RM-1001":
                    assert new_item.net_amount == (old_item.quantity * Decimal("1250.00") * Decimal("0.85")).quantize(Decimal("0.01"))
                else:
                    assert new_item.net_amount == old_item.net_amount

    def test_nothing_changes_before_the_start_date(self):
        seed = seed_with(PriceChange("RM-1001", "0.85", date(2026, 8, 1)))
        assert [o for o in seed.orders if o.order_date < date(2026, 8, 1)] == [o for o in QUIET.orders if o.order_date < date(2026, 8, 1)]


class TestCustomerLoss:
    def test_the_customer_stops_with_contract_still_valid(self):
        seed = seed_with(CustomerLoss(4, date(2026, 8, 10)))
        assert orders_of(seed, EASTERN, date(2026, 8, 10), TODAY) == []
        assert orders_of(seed, EASTERN, date(2026, 8, 1), date(2026, 8, 9))
        assert seed.contracts == QUIET.contracts


class TestCancellations:
    def test_a_share_of_the_customers_orders_in_the_window_is_cancelled(self):
        seed = seed_with(Cancellations(2, 2, 5, date(2026, 8, 1), date(2026, 8, 31)))
        window = orders_of(seed, "0000100003", date(2026, 8, 1), date(2026, 8, 31))
        share = sum(1 for o in window if o.overall_status == "X") / len(window)
        assert 0.35 <= share <= 0.5

    def test_other_customers_and_other_months_keep_their_normal_cancellations(self):
        seed = seed_with(Cancellations(2, 2, 5, date(2026, 8, 1), date(2026, 8, 31)))
        assert orders_of(seed, ACME, date(2026, 8, 1), date(2026, 8, 31)) == orders_of(QUIET, ACME, date(2026, 8, 1), date(2026, 8, 31))
        assert orders_of(seed, "0000100003", date(2026, 9, 1), date(2026, 9, 30)) != []
