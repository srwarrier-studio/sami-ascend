from collections import defaultdict
from datetime import date
from decimal import Decimal

import pytest

from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.inventory_master import GROUP_OF, GROUPS, LOCATIONS
from butterfly.infrastructure.memory.inventory_seed import build_inventory
from butterfly.infrastructure.memory.scenarios import find_scenario
from butterfly.infrastructure.memory.story_seed import build_story_seed
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.money import from_minor, quantity_from_minor
from butterfly.infrastructure.sqlite.seeder import prepare

TODAY = date(2026, 11, 3)
STORY = build_story_seed(TODAY, find_scenario("august-contract"), COMPANIES)
INVENTORY = build_inventory(STORY, COMPANIES, TODAY)
MOVEMENTS = INVENTORY.movements
STOCKS = {s.material: s for s in INVENTORY.stocks}


def sums(type_: str) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for m in MOVEMENTS:
        if m.movement_type == type_:
            totals[m.material] += m.quantity
    return dict(totals)


class TestMasterData:
    def test_every_material_has_a_known_group(self):
        codes = {group.code for group in GROUPS}
        assert set(GROUP_OF.values()) <= codes
        assert set(GROUP_OF) == set(STOCKS)

    def test_every_company_has_a_raw_and_a_finished_store(self):
        assert {(l.company_code, l.code) for l in LOCATIONS} == {(c.code, code) for c in COMPANIES for code in ("0001", "0002")}

    def test_raw_materials_sit_in_the_raw_store_and_products_in_the_finished_store(self):
        for company in COMPANIES:
            assert {STOCKS[r[0]].storage_location for r in company.raw_materials} == {"0001"}
            assert {STOCKS[m[0]].storage_location for m in company.materials} == {"0002"}


class TestStockFollowsFromTheMovements:
    def test_stock_now_is_opening_plus_receipts_minus_issues_and_never_negative(self):
        running: dict[str, Decimal] = defaultdict(Decimal)
        for m in sorted(MOVEMENTS, key=lambda m: m.material_document):
            running[m.material] += m.quantity if m.debit_credit_code == "S" else -m.quantity
            assert running[m.material] >= 0, m
        assert {k: v for k, v in running.items()} == {material: s.stock_quantity for material, s in STOCKS.items()}

    def test_raw_material_receipts_are_the_delivered_quantities_of_the_purchases(self):
        expected: dict[str, Decimal] = defaultdict(Decimal)
        for d in STORY.deliveries:
            if d.delivery_status != "X" and d.actual_delivery_date and d.actual_delivery_date <= TODAY:
                expected[d.material] += d.delivered_quantity
        assert sums("101") == dict(expected)

    def test_receipts_on_the_actual_delivery_date(self):
        by_day = {(m.material, m.posting_date): m.quantity for m in MOVEMENTS if m.movement_type == "101"}
        delivery = next(d for d in STORY.deliveries if d.actual_delivery_date and d.delivery_status != "X")
        assert (delivery.material, delivery.actual_delivery_date) in by_day

    def test_production_receipts_are_the_confirmed_quantities_on_the_end_date(self):
        expected: dict[str, Decimal] = defaultdict(Decimal)
        for p in STORY.production_orders:
            if p.actual_end_date and p.confirmed_quantity > 0:
                expected[p.material] += p.confirmed_quantity
        assert sums("131") == dict(expected)

    def test_production_issues_are_the_components_of_the_started_orders(self):
        started = {p.production_order for p in STORY.production_orders if p.planned_start_date <= TODAY}
        expected: dict[str, Decimal] = defaultdict(Decimal)
        for c in STORY.components:
            if c.production_order in started:
                expected[c.material] += c.required_quantity
        assert sums("261") == dict(expected)

    def test_delivery_issues_are_the_items_of_the_orders_that_are_not_cancelled(self):
        expected: dict[str, Decimal] = defaultdict(Decimal)
        for order in STORY.orders:
            when = order.requested_delivery_date or order.order_date
            if order.overall_status != "X" and when <= TODAY:
                for item in order.items:
                    expected[item.material] += item.quantity
        assert sums("601") == dict(expected)

    def test_nothing_is_posted_in_the_future(self):
        assert max(m.posting_date for m in MOVEMENTS) <= TODAY


class TestStatusAndLevels:
    def test_zero_low_and_ok(self):
        by_status = defaultdict(list)
        for s in INVENTORY.stocks:
            by_status[s.stock_status].append(s)
        assert all(s.stock_quantity == 0 for s in by_status["Z"])
        assert all(0 < s.stock_quantity < s.reorder_level for s in by_status["L"])
        assert all(s.stock_quantity >= s.reorder_level > 0 or s.reorder_level == 0 for s in by_status["O"])
        assert by_status["Z"] and by_status["L"] and by_status["O"]

    def test_zero_stock_comes_from_a_stock_count_posted_today(self):
        for s in INVENTORY.stocks:
            if s.stock_quantity == 0:
                assert s.last_movement_date == TODAY
                assert any(m.material == s.material and m.movement_type == "702" for m in MOVEMENTS)

    def test_the_last_movement_date_is_the_latest_posting_of_the_material(self):
        latest: dict[str, date] = {}
        for m in MOVEMENTS:
            latest[m.material] = max(latest.get(m.material, m.posting_date), m.posting_date)
        assert {k: s.last_movement_date for k, s in STOCKS.items()} == latest

    def test_the_value_is_the_quantity_at_one_price(self):
        for s in INVENTORY.stocks:
            movement = next(m for m in MOVEMENTS if m.material == s.material)
            price = movement.amount / movement.quantity
            assert abs(s.stock_value - s.stock_quantity * price) < Decimal("1.00")


class TestValueByMonth:
    def test_the_latest_month_equals_the_stock_value_per_company(self):
        for company in COMPANIES:
            now = sum((s.stock_value for s in INVENTORY.stocks if s.company_code == company.code), Decimal(0))
            months = [v for v in INVENTORY.monthly if v.company_code == company.code]
            assert months[-1].posting_period == "2026-11"
            assert abs(months[-1].stock_value - now) < Decimal("0.05")

    def test_months_are_consecutive_without_gaps(self):
        months = [v.posting_period for v in INVENTORY.monthly if v.company_code == "INA1"]
        assert months == sorted(months) and len(months) == len(set(months)) == 15

    def test_a_month_end_value_is_what_the_stock_was_then(self):
        end = date(2026, 9, 30)
        value = Decimal(0)
        prices = {s.material: (m.amount / m.quantity) for s in INVENTORY.stocks if s.company_code == "INA1" for m in [next(x for x in MOVEMENTS if x.material == s.material)]}
        running: dict[str, Decimal] = defaultdict(Decimal)
        for m in MOVEMENTS:
            if m.company_code == "INA1" and m.posting_date <= end:
                running[m.material] += m.quantity if m.debit_credit_code == "S" else -m.quantity
        value = sum((q * prices[material] for material, q in running.items()), Decimal(0))
        recorded = next(v for v in INVENTORY.monthly if v.company_code == "INA1" and v.posting_period == "2026-09")
        assert abs(recorded.stock_value - value) < Decimal("1.00")


class TestDocuments:
    def test_numbers_are_unique_and_follow_the_posting_order(self):
        numbers = [m.material_document for m in MOVEMENTS]
        assert numbers == sorted(numbers) and len(set(numbers)) == len(numbers)
        assert [m.posting_date for m in MOVEMENTS] == sorted(m.posting_date for m in MOVEMENTS)

    def test_the_entry_time_is_in_office_hours_on_the_posting_date(self):
        assert {m.entry_date_time.hour for m in MOVEMENTS} <= set(range(8, 18))
        assert all(m.entry_date_time.date() == m.posting_date for m in MOVEMENTS)

    def test_the_year_is_the_posting_year(self):
        assert all(m.material_document_year == str(m.posting_date.year) for m in MOVEMENTS)

    def test_the_same_seed_gives_the_same_stock(self):
        assert build_inventory(STORY, COMPANIES, TODAY) == INVENTORY

    def test_amounts_are_never_negative_and_in_rupees(self):
        assert all(m.amount >= 0 and m.currency == "INR" for m in MOVEMENTS)


class TestInTheDatabase:
    def count(self, db, table):
        return db.query(f"SELECT COUNT(*) AS n FROM {table}")[0]["n"]

    def test_the_story_seed_writes_the_inventory_tables(self):
        db = Database()
        prepare(db, "story", "august-contract", TODAY)
        assert self.count(db, "material_stock") == len(INVENTORY.stocks)
        assert self.count(db, "stock_movement") == len(MOVEMENTS)
        assert self.count(db, "stock_value_month") == len(INVENTORY.monthly)
        assert self.count(db, "material_group") == len(GROUPS)
        assert self.count(db, "storage_location") == len(LOCATIONS)
        assert self.count(db, "material_group_of") == len(GROUP_OF)

    def test_amounts_and_quantities_come_back_exact(self):
        db = Database()
        prepare(db, "story", "august-contract", TODAY)
        row = db.query("SELECT * FROM material_stock WHERE material = 'RAW-2002'")[0]
        assert quantity_from_minor(row["stock_quantity"]) == STOCKS["RAW-2002"].stock_quantity
        assert from_minor(row["stock_value"]) == STOCKS["RAW-2002"].stock_value
        moved = db.query("SELECT SUM(amount) AS s FROM stock_movement WHERE movement_type = '601'")[0]["s"]
        assert from_minor(moved) == sum((m.amount for m in MOVEMENTS if m.movement_type == "601"), Decimal(0))

    def test_the_small_seed_has_no_stock_but_has_the_master_data(self):
        db = Database()
        prepare(db, "small", "august-contract", TODAY)
        assert self.count(db, "material_stock") == 0 and self.count(db, "stock_movement") == 0
        assert self.count(db, "material_group") == len(GROUPS)

    def test_an_older_database_without_the_inventory_is_rebuilt_and_keeps_api_orders(self):
        db = Database()
        prepare(db, "story", "august-contract", TODAY)
        db.execute("INSERT INTO sales_order VALUES ('0000099999', 'OR', '1', NULL, '2026-11-03', NULL, 'INR', 100, 'A', 'ME', '2026-11-03T09:00:00+00:00', '2026-11-03T09:00:00+00:00', 'INA1', 'IN', 'api')")
        db.execute("DELETE FROM meta WHERE key = 'layout'")
        db.execute("DELETE FROM material_stock")
        assert prepare(db, "story", "august-contract", TODAY) is True
        assert self.count(db, "material_stock") == len(INVENTORY.stocks)
        assert db.query("SELECT COUNT(*) AS n FROM sales_order WHERE origin = 'api'")[0]["n"] == 1
