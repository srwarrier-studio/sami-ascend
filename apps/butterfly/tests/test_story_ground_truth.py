from collections import defaultdict
from datetime import date
from decimal import Decimal

from butterfly.infrastructure.memory.story_seed import build_story_seed

TODAY = date(2026, 10, 31)
SEED = build_story_seed(TODAY)
ACME = "0000100001"
STEEL_PLATE = "RM-1002"
LIVE = [o for o in SEED.orders if o.overall_status != "X"]


def month_of(day: date) -> tuple[int, int]:
    return (day.year, day.month)


def total(month: tuple[int, int], keep=lambda order: True) -> Decimal:
    return sum((o.total_net_amount for o in LIVE if month_of(o.order_date) == month and keep(o)), Decimal(0))


def steel_plate_sales(month: tuple[int, int], keep=lambda order: True) -> Decimal:
    return sum((i.net_amount for o in LIVE if month_of(o.order_date) == month and keep(o) for i in o.items if i.material == STEEL_PLATE), Decimal(0))


def material_sales(month: tuple[int, int], material: str) -> Decimal:
    return sum((i.net_amount for o in LIVE if month_of(o.order_date) == month for i in o.items if i.material == material), Decimal(0))


def percent(part: Decimal, whole: Decimal) -> float:
    return float(part / whole * 100)


JUNE, JULY, AUGUST, SEPTEMBER, OCTOBER = (2026, 6), (2026, 7), (2026, 8), (2026, 9), (2026, 10)
BASELINE = [(2025, 9), (2025, 10), (2025, 11), (2025, 12), (2026, 1), (2026, 2), (2026, 3), (2026, 4), (2026, 5)]
FALL = total(JULY) - total(AUGUST)
ACME_LOSS = total(JULY, lambda o: o.sold_to_party == ACME) - total(AUGUST, lambda o: o.sold_to_party == ACME)
SHORTAGE_LOSS = steel_plate_sales(JULY, lambda o: o.sold_to_party != ACME) - steel_plate_sales(AUGUST, lambda o: o.sold_to_party != ACME)
OTHER = FALL - ACME_LOSS - SHORTAGE_LOSS


class TestTheFall:
    def test_august_is_thirteen_to_sixteen_percent_below_july(self):
        assert -16 <= percent(total(AUGUST) - total(JULY), total(JULY)) <= -13

    def test_july_was_already_lower_than_june(self):
        assert -16 <= percent(total(JULY) - total(JUNE), total(JUNE)) <= -10

    def test_sales_recover_after_the_contract_is_renewed_and_the_steel_arrives(self):
        assert total(SEPTEMBER) > total(AUGUST)
        average = sum(total(m) for m in BASELINE) / len(BASELINE)
        assert abs(total(OCTOBER) - average) / average < Decimal("0.05")

    def test_the_months_before_the_story_are_steady(self):
        average = sum(total(m) for m in BASELINE) / len(BASELINE)
        assert all(abs(total(m) - average) / average < Decimal("0.05") for m in BASELINE)


class TestWhatExplainsTheFall:
    def test_the_three_parts_add_up_to_the_fall(self):
        assert ACME_LOSS + SHORTAGE_LOSS + OTHER == FALL

    def test_acme_is_the_biggest_part(self):
        assert 70 <= percent(ACME_LOSS, FALL) <= 90
        assert ACME_LOSS > SHORTAGE_LOSS

    def test_the_steel_plate_shortage_on_the_other_customers_is_the_second_part(self):
        assert 30 <= percent(SHORTAGE_LOSS, FALL) <= 50

    def test_the_rest_of_the_business_grew_a_little_and_offsets_part_of_it(self):
        assert -30 <= percent(OTHER, FALL) <= -10

    def test_acme_is_the_biggest_customer_over_the_normal_months_at_about_a_fifth_of_sales(self):
        customers = {o.sold_to_party for o in LIVE}
        over_baseline = {c: sum(total(m, lambda o, c=c: o.sold_to_party == c) for m in BASELINE) for c in customers}
        assert max(over_baseline, key=over_baseline.get) == ACME
        assert 19 <= percent(over_baseline[ACME], sum(over_baseline.values())) <= 24

    def test_acme_is_never_a_tiny_or_dominant_share_of_a_normal_month(self):
        assert all(16 <= percent(total(m, lambda o: o.sold_to_party == ACME), total(m)) <= 26 for m in BASELINE)

    def test_acme_has_almost_nothing_in_august(self):
        assert percent(total(AUGUST, lambda o: o.sold_to_party == ACME), total(AUGUST)) < 2

    def test_steel_plate_is_a_sixth_of_normal_sales_and_falls_by_more_than_half_of_that_in_august(self):
        normal = sum(percent(steel_plate_sales(m), total(m)) for m in BASELINE) / len(BASELINE)
        assert 12 <= normal <= 22
        assert steel_plate_sales(AUGUST) < Decimal("0.7") * steel_plate_sales(JUNE)


class TestTheDecoys:
    def test_the_late_copper_rod_in_may_did_not_change_copper_wire_sales(self):
        normal = sum(material_sales(m, "RM-1003") for m in BASELINE if m != (2026, 5)) / (len(BASELINE) - 1)
        assert abs(material_sales((2026, 5), "RM-1003") - normal) / normal < Decimal("0.12")

    def test_the_bearing_machine_breakdown_in_may_did_not_change_bearing_sales(self):
        normal = sum(material_sales(m, "RM-1005") for m in BASELINE if m != (2026, 5)) / (len(BASELINE) - 1)
        assert abs(material_sales((2026, 5), "RM-1005") - normal) / normal < Decimal("0.12")

    def test_the_decoys_are_real_events_in_the_data(self):
        late = [d for d in SEED.deliveries if d.supplier_name == "Kalyani Wire Industries" and d.actual_delivery_date and (d.actual_delivery_date - d.promised_delivery_date).days == 4]
        broken = [p for p in SEED.production_orders if p.delay_reason == "MACHINE_BREAKDOWN"]
        assert len(late) == 1 and len(broken) == 1


class TestTheChainOfCauses:
    def test_the_events_happen_in_the_order_that_explains_the_fall(self):
        contract = next(c for c in SEED.contracts if c.sales_contract == "0040000127")
        delivery = next(d for d in SEED.deliveries if d.purchase_order == "4500001207")
        production = next(p for p in SEED.production_orders if p.production_order == "0001000417")
        assert contract.valid_to < date(2026, 7, 13)
        assert delivery.promised_delivery_date < production.planned_end_date < delivery.actual_delivery_date < production.actual_end_date
        assert production.planned_end_date == date(2026, 7, 20)

    def test_acme_orders_stop_the_day_after_the_contract_ends(self):
        last_regular = max(o.order_date for o in SEED.orders if o.sold_to_party == ACME and len(o.items) > 1 and o.order_date < date(2026, 9, 14))
        assert date(2026, 7, 10) <= last_regular <= date(2026, 7, 12)

    def test_steel_plate_orders_drop_from_the_day_the_late_production_was_due_to_finish(self):
        def per_day(start, end):
            others = [o for o in SEED.orders if o.sold_to_party != ACME and start <= o.order_date <= end]
            return sum(1 for o in others for i in o.items if i.material == STEEL_PLATE) / len({o.order_date for o in others})

        before = per_day(date(2026, 7, 1), date(2026, 7, 17))
        during = per_day(date(2026, 7, 20), date(2026, 7, 31))
        assert during < 0.8 * before
