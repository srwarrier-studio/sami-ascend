import json
from datetime import date
from decimal import Decimal
from pathlib import Path

import pytest

from butterfly.domain.entities.scenario import Cancellations, Drop, PriceChange
from butterfly.infrastructure.memory.scenarios import SCENARIOS
from butterfly.infrastructure.memory.story_seed import RAW_MATERIALS, build_story_seed

TODAY = date(2026, 10, 31)
FOLDER = Path(__file__).resolve().parent.parent / "scenarios"
TRUTHS = {path.stem: json.loads(path.read_text()) for path in sorted(FOLDER.glob("*.json"))}
BY_NAME = {s.name: s for s in SCENARIOS}
MATERIAL_OF_RAW = {raw[0]: raw[4] for raw in RAW_MATERIALS}


def month_of(text: str) -> tuple[int, int]:
    year, month = text.split("-")
    return (int(year), int(month))


def value(seed, month, material=None, customer=None) -> Decimal:
    return sum(
        (
            i.net_amount
            for o in seed.orders
            if o.overall_status != "X" and (o.order_date.year, o.order_date.month) == month
            and customer in (None, o.sold_to_party)
            for i in o.items
            if material in (None, i.material)
        ),
        Decimal(0),
    )


def volume(seed, month, material) -> Decimal:
    return sum((i.quantity for o in seed.orders if o.overall_status != "X" and (o.order_date.year, o.order_date.month) == month for i in o.items if i.material == material), Decimal(0))


def change(before: Decimal, after: Decimal) -> float:
    return float((after - before) / before * 100)


def seed_of(name: str):
    return build_story_seed(TODAY, BY_NAME[name])


class TestTheDataHoldsTheGroundTruth:
    @pytest.mark.parametrize("name", sorted(TRUTHS))
    def test_total_sales_change_is_in_the_stated_range(self, name):
        truth, seed = TRUTHS[name], seed_of(name)
        low, high = truth["total_change_percent"]
        assert low <= change(value(seed, month_of(truth["compare_with"])), value(seed, month_of(truth["month"]))) <= high

    @pytest.mark.parametrize("name", sorted(TRUTHS))
    def test_the_product_change_is_in_the_stated_ranges(self, name):
        truth, seed = TRUTHS[name], seed_of(name)
        if "product" not in truth:
            pytest.skip("no product block")
        product, month, before = truth["product"], month_of(truth["month"]), month_of(truth["compare_with"])
        low, high = product["value_change_percent"]
        assert low <= change(value(seed, before, product["material"]), value(seed, month, product["material"])) <= high
        low, high = product["volume_change_percent"]
        assert low <= change(volume(seed, before, product["material"]), volume(seed, month, product["material"])) <= high

    @pytest.mark.parametrize("name", sorted(TRUTHS))
    def test_the_biggest_mover_is_the_named_customer(self, name):
        truth, seed = TRUTHS[name], seed_of(name)
        if "biggest_mover" not in truth:
            pytest.skip("no biggest mover")
        month, before = month_of(truth["month"]), month_of(truth["compare_with"])
        customers = {o.sold_to_party for o in seed.orders}
        moves = {c: value(seed, month, customer=c) - value(seed, before, customer=c) for c in customers}
        assert min(moves, key=moves.get) == truth["biggest_mover"]

    @pytest.mark.parametrize("name", sorted(TRUTHS))
    def test_every_cause_exists_and_is_what_it_says(self, name):
        truth, seed = TRUTHS[name], seed_of(name)
        month = month_of(truth["month"])
        for cause in truth["causes"]:
            key = cause["key"]
            if cause["type"] == "contract":
                contract = next(c for c in seed.contracts if c.sales_contract == key)
                assert (contract.valid_to.year, contract.valid_to.month) < month
            elif cause["type"] == "purchase_delivery":
                delivery = next(d for d in seed.deliveries if d.purchase_order == key)
                assert (delivery.actual_delivery_date - delivery.promised_delivery_date).days >= 5
            elif cause["type"] == "production_order":
                assert next(p for p in seed.production_orders if p.production_order == key).delay_reason
            elif cause["type"] == "price_change":
                assert any(isinstance(e, PriceChange) and e.material == key for e in BY_NAME[name].events)
            elif cause["type"] == "cancelled_orders":
                orders = [o for o in seed.orders if o.sold_to_party == key and (o.order_date.year, o.order_date.month) == month]
                assert sum(1 for o in orders if o.overall_status == "X") / len(orders) >= 0.3
                assert any(isinstance(e, Cancellations) for e in BY_NAME[name].events)
            else:
                pytest.fail(f"unknown cause type {cause['type']}")

    @pytest.mark.parametrize("name", sorted(TRUTHS))
    def test_what_must_not_be_blamed_exists_and_has_no_effect_on_sales(self, name):
        truth, seed = TRUTHS[name], seed_of(name)
        drops = [e.drop for e in BY_NAME[name].events if getattr(e, "drop", None)]
        for item in truth["not_blame"]:
            if item["type"] == "purchase_delivery":
                row = next(d for d in seed.deliveries if d.purchase_order == item["key"])
                material = MATERIAL_OF_RAW[row.material]
            else:
                row = next(p for p in seed.production_orders if p.production_order == item["key"])
                material = row.material
            assert not any(isinstance(d, Drop) and d.material == material for d in drops)

    @pytest.mark.parametrize("name", sorted(TRUTHS))
    def test_something_left_unexplained_has_no_event_behind_it(self, name):
        truth, seed = TRUTHS[name], seed_of(name)
        if not truth["unexplained"]:
            pytest.skip("everything is explained")
        month = month_of(truth["month"])
        assert truth["causes"] == []
        end = date(month[0], month[1], 28)
        contracts = [c for c in seed.contracts if c.sold_to_party == truth["biggest_mover"]]
        assert any(c.valid_from <= end <= c.valid_to for c in contracts)
