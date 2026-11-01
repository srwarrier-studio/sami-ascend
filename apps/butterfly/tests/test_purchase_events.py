from datetime import date
from decimal import Decimal

from butterfly.domain.entities.scenario import (
    DemandGrowth,
    PurchasePriceChange,
    PurchaseQuantityChange,
    Scenario,
    SupplierSwitch,
)
from butterfly.infrastructure.memory.story_seed import build_story_seed

TODAY = date(2026, 10, 31)
QUIET = build_story_seed(TODAY, Scenario("test", ()))


def seed_with(*events):
    return build_story_seed(TODAY, Scenario("test", events))


def pairs(seed, kind):
    return list(zip(getattr(QUIET, kind), getattr(seed, kind)))


def deliveries_of(seed, material):
    return [(a, b) for a, b in pairs(seed, "deliveries") if a.material == material]


class TestPurchasePriceChange:
    SEED = seed_with(PurchasePriceChange("RAW-2002", "1.2", date(2026, 8, 1)))

    def test_amounts_rise_from_the_start_date_and_quantities_do_not(self):
        rows = [(a, b) for a, b in deliveries_of(self.SEED, "RAW-2002") if a.order_date >= date(2026, 8, 1)]
        assert rows
        for old, new in rows:
            assert new.ordered_quantity == old.ordered_quantity
            assert new.net_amount == (old.net_amount * Decimal("1.2")).quantize(Decimal("0.01"))

    def test_nothing_changes_before_the_start_date_or_for_other_materials(self):
        for old, new in pairs(self.SEED, "deliveries"):
            if new.material != "RAW-2002" or new.order_date < date(2026, 8, 1):
                assert old == new

    def test_sales_and_production_are_untouched(self):
        assert self.SEED.orders == QUIET.orders and self.SEED.production_orders == QUIET.production_orders


class TestPurchaseQuantityChange:
    SEED = seed_with(PurchaseQuantityChange("RAW-2003", "1.6", date(2026, 9, 1), date(2026, 9, 30)))

    def test_only_orders_placed_in_the_window_are_larger(self):
        changed = [(a, b) for a, b in deliveries_of(self.SEED, "RAW-2003") if a != b]
        assert len(changed) == 1
        old, new = changed[0]
        assert date(2026, 9, 1) <= old.order_date <= date(2026, 9, 30)
        assert new.ordered_quantity == old.ordered_quantity * Decimal("1.6")
        assert new.net_amount == old.net_amount * Decimal("1.6")

    def test_price_per_unit_is_unchanged(self):
        [(old, new)] = [(a, b) for a, b in deliveries_of(self.SEED, "RAW-2003") if a != b]
        assert new.net_amount / new.ordered_quantity == old.net_amount / old.ordered_quantity

    def test_delivered_quantity_follows_for_a_delivered_item(self):
        for old, new in deliveries_of(self.SEED, "RAW-2003"):
            if new.delivery_status == "D":
                assert new.delivered_quantity == new.ordered_quantity


class TestSupplierSwitch:
    SEED = seed_with(SupplierSwitch("RAW-2005", 1, "1.15", date(2026, 10, 1)))

    def test_orders_from_the_start_date_come_from_the_new_supplier_at_the_new_price(self):
        [(old, new)] = [(a, b) for a, b in deliveries_of(self.SEED, "RAW-2005") if a != b]
        assert old.order_date >= date(2026, 10, 1)
        assert (old.supplier_name, new.supplier_name) == ("Pack-Rite Industries Pvt Ltd", "Malnad Botanicals Pvt Ltd")
        assert new.supplier == "0000200002"
        assert new.net_amount == (old.net_amount * Decimal("1.15")).quantize(Decimal("0.01"))
        assert new.ordered_quantity == old.ordered_quantity

    def test_earlier_orders_stay_with_the_old_supplier(self):
        assert all(a == b for a, b in deliveries_of(self.SEED, "RAW-2005") if a.order_date < date(2026, 10, 1))


class TestDemandGrowth:
    SEED = seed_with(DemandGrowth("RM-1002", "1.35", date(2026, 6, 15)))

    def test_sales_of_the_product_grow_from_the_start_date(self):
        old_items = [(i, o.order_date) for o in QUIET.orders for i in o.items if i.material == "RM-1002"]
        new_items = [(i, o.order_date) for o in self.SEED.orders for i in o.items if i.material == "RM-1002"]
        assert len(old_items) == len(new_items)
        for (old, day), (new, _) in zip(old_items, new_items):
            expected = old.quantity if day < date(2026, 6, 15) else (old.quantity * Decimal("1.35"))
            assert abs(new.quantity - expected) <= Decimal("0.002")

    def test_other_products_are_not_sold_more(self):
        old = sum(i.quantity for o in QUIET.orders for i in o.items if i.material == "RM-1001" and o.order_date >= date(2026, 7, 1))
        new = sum(i.quantity for o in self.SEED.orders for i in o.items if i.material == "RM-1001" and o.order_date >= date(2026, 7, 1))
        assert new == old

    def test_production_plans_more_from_the_month_after_the_start(self):
        for old, new in pairs(self.SEED, "production_orders"):
            if new.material == "RM-1002" and old.planned_start_date >= date(2026, 7, 1):
                assert new.planned_quantity == (old.planned_quantity * Decimal("1.35")).quantize(Decimal("0.001"))
            else:
                assert old == new

    def test_the_first_grown_production_order_is_the_one_planned_for_july(self):
        grown = [new for old, new in pairs(self.SEED, "production_orders") if old != new]
        assert min(p.planned_start_date for p in grown) >= date(2026, 7, 1)

    def test_components_of_the_grown_orders_need_more(self):
        grown = {new.production_order for old, new in pairs(self.SEED, "production_orders") if old != new}
        for old, new in pairs(self.SEED, "components"):
            if new.production_order in grown:
                assert new.required_quantity > old.required_quantity
            else:
                assert old == new

    def test_purchases_of_the_raw_material_grow_from_orders_placed_two_months_after_the_start(self):
        for old, new in deliveries_of(self.SEED, "RAW-2002"):
            if old.order_date >= date(2026, 8, 1):
                assert new.ordered_quantity == (old.ordered_quantity * Decimal("1.35")).quantize(Decimal("0.001"))
            else:
                assert old == new

    def test_other_raw_materials_are_not_bought_more(self):
        assert all(a == b for a, b in pairs(self.SEED, "deliveries") if a.material != "RAW-2002")

    def test_the_chain_happens_in_order(self):
        sales = min(o.order_date for o in self.SEED.orders if o.order_date >= date(2026, 6, 15))
        production = min(new.planned_start_date for old, new in pairs(self.SEED, "production_orders") if old != new)
        purchase = min(new.order_date for old, new in pairs(self.SEED, "deliveries") if old != new)
        assert sales < production < purchase
