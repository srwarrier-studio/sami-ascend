from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal

from butterfly.infrastructure.memory.seed import CUSTOMERS, MATERIALS
from butterfly.infrastructure.memory.story_seed import STORY_START, build_story_seed

TODAY = date(2026, 10, 31)
SEED = build_story_seed(TODAY)
HARBORLINE = "0000100001"
CONTRACTS = {c.sales_contract: c for c in SEED.contracts}
DELIVERIES = {d.purchase_order: d for d in SEED.deliveries}
PRODUCTION = {p.production_order: p for p in SEED.production_orders}


class TestContracts:
    def test_harborline_has_three_linked_contracts_with_a_gap_in_the_middle(self):
        first, second, third = (CONTRACTS[n] for n in ("0040000071", "0040000127", "0040000163"))
        assert first.predecessor_contract is None
        assert (second.predecessor_contract, third.predecessor_contract) == ("0040000071", "0040000127")
        assert (second.valid_from, second.valid_to) == (date(2025, 7, 13), date(2026, 7, 12))
        assert (third.valid_from, third.valid_to) == (date(2026, 9, 14), date(2027, 9, 13))
        assert (first.contract_status, second.contract_status, third.contract_status) == ("E", "E", "A")
        assert all(c.sold_to_party == HARBORLINE and c.customer_name == "Harborline Nutrition LLC" for c in (first, second, third))

    def test_every_other_customer_has_a_contract_valid_on_every_day_of_the_story(self):
        others = [c for c in SEED.contracts if c.sold_to_party != HARBORLINE]
        day = STORY_START
        while day <= TODAY:
            for customer_id, _ in CUSTOMERS[1:]:
                assert any(c.sold_to_party == customer_id and c.valid_from <= day <= c.valid_to for c in others), (customer_id, day)
            day += timedelta(days=7)

    def test_status_follows_the_dates(self):
        for contract in SEED.contracts:
            assert contract.contract_status == ("A" if contract.valid_to >= TODAY else "E")

    def test_a_contract_that_has_not_started_yet_is_left_out(self):
        early = build_story_seed(date(2026, 9, 1))
        assert "0040000163" not in {c.sales_contract for c in early.contracts}

    def test_every_contract_belongs_to_a_known_customer(self):
        assert {c.sold_to_party for c in SEED.contracts} == {cid for cid, _ in CUSTOMERS}


class TestDeliveries:
    def test_deccan_agro_delivered_black_pepper_twelve_days_late(self):
        row = DELIVERIES["4500001207"]
        assert (row.supplier, row.supplier_name) == ("0000200001", "Deccan Agro Growers Cooperative")
        assert (row.material, row.material_description) == ("RAW-2002", "Black pepper, whole")
        assert (row.order_date, row.promised_delivery_date, row.actual_delivery_date) == (date(2026, 6, 24), date(2026, 7, 14), date(2026, 7, 26))
        assert (row.ordered_quantity, row.delivered_quantity, row.delivery_status) == (Decimal("5000.000"), Decimal("5000.000"), "D")

    def test_a_frankincense_delivery_in_may_was_four_days_late(self):
        row = DELIVERIES["4500001196"]
        assert (row.supplier_name, row.material) == ("Malnad Botanicals Pvt Ltd", "RAW-2003")
        assert (row.actual_delivery_date - row.promised_delivery_date).days == 4 and row.promised_delivery_date.month == 5

    def test_those_are_the_only_deliveries_more_than_two_days_late(self):
        late = {d.purchase_order for d in SEED.deliveries if d.actual_delivery_date and (d.actual_delivery_date - d.promised_delivery_date).days > 2}
        assert late == {"4500001207", "4500001196"}

    def test_one_purchase_order_per_raw_material_per_month_with_unique_numbers(self):
        assert len(DELIVERIES) == len(SEED.deliveries)
        per_month = Counter((d.promised_delivery_date.year, d.promised_delivery_date.month) for d in SEED.deliveries)
        assert set(per_month.values()) == {6}

    def test_next_months_deliveries_are_open_with_nothing_received(self):
        open_rows = [d for d in SEED.deliveries if d.delivery_status == "O"]
        assert open_rows and all(d.actual_delivery_date is None and d.delivered_quantity == 0 for d in open_rows)
        assert all(d.promised_delivery_date > TODAY for d in open_rows)

    def test_delivered_rows_have_an_actual_date_not_in_the_future(self):
        for d in SEED.deliveries:
            if d.delivery_status == "D":
                assert d.actual_delivery_date and d.actual_delivery_date <= TODAY and d.delivered_quantity == d.ordered_quantity

    def test_every_supplier_supplies_two_raw_materials(self):
        by_supplier = defaultdict(set)
        for d in SEED.deliveries:
            by_supplier[d.supplier_name].add(d.material)
        assert {name: len(materials) for name, materials in by_supplier.items()} == {"Deccan Agro Growers Cooperative": 2, "Malnad Botanicals Pvt Ltd": 2, "Pack-Rite Industries Pvt Ltd": 2}


class TestProduction:
    def test_piperine_finished_fourteen_days_late_for_lack_of_black_pepper(self):
        row = PRODUCTION["0001000417"]
        assert (row.material, row.material_description) == ("RM-1002", "Piperine extract 95%")
        assert (row.planned_start_date, row.planned_end_date, row.actual_end_date) == (date(2026, 7, 6), date(2026, 7, 20), date(2026, 8, 3))
        assert (row.production_status, row.delay_reason) == ("C", "MATERIAL_SHORTAGE")
        assert row.confirmed_quantity == row.planned_quantity

    def test_probiotic_capsules_were_late_in_may_because_a_machine_broke_down(self):
        row = PRODUCTION["0001000408"]
        assert (row.material, row.planned_end_date.month, row.delay_reason) == ("RM-1005", 5, "MACHINE_BREAKDOWN")
        assert (row.actual_end_date - row.planned_end_date).days == 6

    def test_those_are_the_only_late_orders(self):
        assert {p.production_order for p in SEED.production_orders if p.delay_reason} == {"0001000417", "0001000408"}
        assert all(p.actual_end_date == p.planned_end_date for p in SEED.production_orders if not p.delay_reason and p.actual_end_date)

    def test_the_next_order_for_a_product_starts_after_the_previous_one_ended(self):
        by_product = defaultdict(list)
        for p in SEED.production_orders:
            by_product[p.material].append(p)
        for orders in by_product.values():
            for before, after in zip(orders, orders[1:]):
                assert after.planned_start_date > before.actual_end_date

    def test_every_product_has_an_order_every_month_and_next_months_are_running(self):
        assert Counter(p.material for p in SEED.production_orders) == {m[0]: 15 for m in MATERIALS}
        running = [p for p in SEED.production_orders if p.production_status == "R"]
        assert running and all(p.actual_end_date is None and p.confirmed_quantity == 0 and p.delay_reason is None for p in running)

    def test_each_order_has_one_component_that_is_the_raw_material_of_its_product(self):
        assert {c.production_order for c in SEED.components} == set(PRODUCTION)
        assert len(SEED.components) == len(SEED.production_orders)
        raw = {"RM-1001": "RAW-2001", "RM-1002": "RAW-2002", "RM-1003": "RAW-2003", "RM-1004": "RAW-2004", "RM-1005": "RAW-2005", "RM-1006": "RAW-2006"}
        for component in SEED.components:
            assert component.material == raw[PRODUCTION[component.production_order].material]
            assert component.required_quantity > PRODUCTION[component.production_order].planned_quantity

    def test_the_late_piperine_order_uses_the_late_black_pepper(self):
        component = next(c for c in SEED.components if c.production_order == "0001000417")
        assert (component.material, component.material_description, component.required_quantity) == ("RAW-2002", "Black pepper, whole", Decimal("4400.000"))
        delivery = DELIVERIES["4500001207"]
        assert delivery.material == component.material and delivery.promised_delivery_date <= PRODUCTION["0001000417"].planned_end_date < delivery.actual_delivery_date


class TestSalesHistory:
    def test_orders_run_every_working_day_from_the_start_to_today(self):
        days = {o.order_date for o in SEED.orders}
        assert min(days) == STORY_START and max(days) == date(2026, 10, 30)
        assert all(day.weekday() < 5 for day in days)
        expected = {STORY_START + timedelta(days=n) for n in range((TODAY - STORY_START).days + 1) if (STORY_START + timedelta(days=n)).weekday() < 5}
        assert days == expected

    def test_three_to_six_orders_a_day(self):
        per_day = Counter(o.order_date for o in SEED.orders)
        assert 3 <= min(per_day.values()) and max(per_day.values()) <= 6

    def test_numbers_are_unique_and_in_date_order(self):
        numbers = [o.sales_order for o in SEED.orders]
        assert numbers == sorted(numbers) and len(set(numbers)) == len(numbers)
        assert [o.order_date for o in SEED.orders] == sorted(o.order_date for o in SEED.orders)

    def test_totals_add_up_and_names_come_from_the_master_data(self):
        customers = dict(CUSTOMERS)
        materials = {m[0]: m[1] for m in MATERIALS}
        for order in SEED.orders:
            assert order.total_net_amount == sum(i.net_amount for i in order.items)
            assert customers[order.sold_to_party] == order.customer_name
            assert all(materials[i.material] == i.material_description for i in order.items)
            assert [i.sales_order_item for i in order.items] == [f"{(n + 1) * 10:06d}" for n in range(len(order.items))]

    def test_old_orders_are_settled_and_some_are_cancelled(self):
        statuses = Counter(o.overall_status for o in SEED.orders)
        assert set(statuses) <= {"A", "B", "C", "X"} and 0 < statuses["X"] < len(SEED.orders) / 10
        assert all(o.overall_status in ("C", "X") for o in SEED.orders if (TODAY - o.order_date).days > 30)

    def test_harborline_stops_ordering_after_the_contract_ends_except_for_a_few_small_spot_orders(self):
        gap = [o for o in SEED.orders if o.sold_to_party == HARBORLINE and date(2026, 7, 12) < o.order_date < date(2026, 9, 14)]
        assert 2 <= len(gap) <= 6 and all(len(o.items) == 1 for o in gap)
        regular = [o for o in SEED.orders if o.sold_to_party == HARBORLINE and o.order_date <= date(2026, 7, 12)]
        assert len(regular) > 100 and max(len(o.items) for o in regular) == 3

    def test_harborline_orders_normally_again_after_the_renewal(self):
        after = [o for o in SEED.orders if o.sold_to_party == HARBORLINE and o.order_date >= date(2026, 9, 14)]
        assert len(after) > 25

    def test_piperine_is_ordered_less_while_the_black_pepper_is_missing(self):
        def per_day(start, end):
            others = [o for o in SEED.orders if o.sold_to_party != HARBORLINE and start <= o.order_date <= end]
            days = {o.order_date for o in others}
            return sum(1 for o in others for i in o.items if i.material == "RM-1002") / len(days)

        normal = per_day(date(2026, 4, 1), date(2026, 7, 17))
        short = per_day(date(2026, 7, 20), date(2026, 8, 31))
        after = per_day(date(2026, 9, 1), date(2026, 10, 30))
        assert 0.45 * normal <= short <= 0.8 * normal
        assert after > 0.9 * normal

    def test_months_before_the_story_have_steady_sales(self):
        totals = defaultdict(Decimal)
        for o in SEED.orders:
            if o.overall_status != "X" and date(2025, 9, 1) <= o.order_date <= date(2026, 6, 30):
                totals[(o.order_date.year, o.order_date.month)] += o.total_net_amount
        average = sum(totals.values()) / len(totals)
        assert len(totals) == 10 and all(abs(value - average) / average < Decimal("0.05") for value in totals.values())


class TestRepeatability:
    def test_the_same_day_gives_the_same_data(self):
        again = build_story_seed(TODAY)
        assert again == SEED

    def test_a_later_today_does_not_change_the_history(self):
        earlier = build_story_seed(date(2026, 9, 30))
        settled = [o for o in SEED.orders if o.order_date <= date(2026, 8, 30)]
        assert [o for o in earlier.orders if o.order_date <= date(2026, 8, 30)] == settled
        as_of_september = [o for o in SEED.orders if o.order_date <= date(2026, 9, 30)]
        assert len(as_of_september) == len(earlier.orders)
        assert [(o.sales_order, o.order_date, o.total_net_amount, o.items) for o in as_of_september] == [(o.sales_order, o.order_date, o.total_net_amount, o.items) for o in earlier.orders]
