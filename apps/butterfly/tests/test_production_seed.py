from collections import defaultdict
from datetime import date, timedelta
from decimal import Decimal

from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.production_master import LINES, SCRAP_REASONS, SHIFTS, WORK_CENTERS
from butterfly.infrastructure.memory.production_seed import build_production
from butterfly.infrastructure.memory.scenarios import find_scenario
from butterfly.infrastructure.memory.story_seed import build_story_seed
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.money import from_minor, quantity_from_minor
from butterfly.infrastructure.sqlite.seeder import prepare

TODAY = date(2026, 11, 3)
STORY = build_story_seed(TODAY, find_scenario("august-contract"), COMPANIES)
PRODUCTION = build_production(STORY, COMPANIES, TODAY)
ORDERS = {p.production_order: p for p in STORY.production_orders}


def per_order(field: str) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for c in PRODUCTION.confirmations:
        totals[c.production_order] += getattr(c, field)
    return dict(totals)


class TestConfirmations:
    def test_the_yields_of_a_completed_order_add_up_to_its_confirmed_quantity(self):
        yields = per_order("yield_quantity")
        for number, order in ORDERS.items():
            if order.actual_end_date and order.confirmed_quantity > 0:
                assert yields[number] == order.confirmed_quantity, number

    def test_the_targets_add_up_to_the_planned_quantity(self):
        targets = per_order("target_quantity")
        for number, total in targets.items():
            assert total == ORDERS[number].planned_quantity

    def test_orders_that_have_not_started_have_no_confirmations(self):
        started = {c.production_order for c in PRODUCTION.confirmations}
        assert all(p.production_order not in started for p in STORY.production_orders if p.planned_start_date > TODAY)
        assert len(started) == sum(1 for p in STORY.production_orders if p.actual_end_date)

    def test_confirmations_fall_between_the_start_and_the_actual_end_and_never_on_sunday(self):
        for c in PRODUCTION.confirmations:
            order = ORDERS[c.production_order]
            assert order.planned_start_date <= c.posting_date <= order.actual_end_date and c.posting_date.weekday() != 6

    def test_scrap_has_a_reason_exactly_when_something_was_scrapped(self):
        for c in PRODUCTION.confirmations:
            assert (c.scrap_quantity > 0) == (c.scrap_reason is not None)
            assert c.scrap_reason is None or c.scrap_reason in SCRAP_REASONS
        assert any(c.scrap_reason is None for c in PRODUCTION.confirmations)

    def test_scrap_is_a_small_share_of_the_yield(self):
        yields, scrap = sum(c.yield_quantity for c in PRODUCTION.confirmations), sum(c.scrap_quantity for c in PRODUCTION.confirmations)
        assert Decimal("0.005") < scrap / yields < Decimal("0.04")

    def test_value_is_the_quantity_at_the_standard_price(self):
        for c in PRODUCTION.confirmations[:200]:
            assert abs(c.yield_value - c.yield_quantity * (c.target_value / c.target_quantity)) < Decimal("1.00")
            assert c.currency == "INR"

    def test_lines_shifts_and_hours(self):
        assert {c.work_center for c in PRODUCTION.confirmations} == {f"LINE{n}" for n in range(1, LINES + 1)}
        assert {c.shift for c in PRODUCTION.confirmations} == set(SHIFTS)
        assert {c.run_hours for c in PRODUCTION.confirmations} == {Decimal("8.00")}

    def test_numbers_are_unique_and_follow_the_posting_order(self):
        numbers = [c.confirmation_number for c in PRODUCTION.confirmations]
        assert numbers == sorted(numbers) and len(set(numbers)) == len(numbers)
        assert [c.posting_date for c in PRODUCTION.confirmations] == sorted(c.posting_date for c in PRODUCTION.confirmations)

    def test_the_same_seed_gives_the_same_shop_floor(self):
        assert build_production(STORY, COMPANIES, TODAY) == PRODUCTION


class TestDowntime:
    def test_every_delayed_order_has_a_stoppage_of_its_cause_with_eight_hours_a_day_late(self):
        causes = {"MACHINE_BREAKDOWN": "BREAKDOWN", "MATERIAL_SHORTAGE": "NO_MATERIAL"}
        delayed = [p for p in STORY.production_orders if p.delay_reason]
        assert delayed
        for order in delayed:
            late = (order.actual_end_date - order.planned_end_date).days
            found = [d for d in PRODUCTION.downtimes if d.production_order == order.production_order and d.downtime_cause == causes[order.delay_reason]]
            assert [d.downtime_hours for d in found] == [Decimal(late * 8).quantize(Decimal("0.01"))]

    def test_each_order_changes_over_on_its_first_confirmed_day(self):
        firsts = {}
        for c in PRODUCTION.confirmations:
            firsts.setdefault(c.production_order, c.posting_date)
        changeovers = {d.production_order: d.posting_date for d in PRODUCTION.downtimes if d.downtime_cause == "CHANGEOVER"}
        assert changeovers == firsts

    def test_every_line_is_maintained_each_month_it_runs(self):
        months = {(c.company_code, c.work_center, c.posting_date.year, c.posting_date.month) for c in PRODUCTION.confirmations}
        maintained = {(d.company_code, d.work_center, d.posting_date.year, d.posting_date.month) for d in PRODUCTION.downtimes if d.downtime_cause == "MAINTENANCE"}
        assert maintained == months

    def test_no_stoppage_is_posted_on_a_day_without_confirmations_of_its_company(self):
        days = {(c.company_code, c.posting_date) for c in PRODUCTION.confirmations}
        assert all((d.company_code, d.posting_date) in days for d in PRODUCTION.downtimes)

    def test_hours_have_two_decimals_and_causes_are_known(self):
        assert {d.downtime_cause for d in PRODUCTION.downtimes} <= {"BREAKDOWN", "CHANGEOVER", "NO_MATERIAL", "MAINTENANCE", "OTHER"}
        assert all(d.downtime_hours == d.downtime_hours.quantize(Decimal("0.01")) and d.downtime_hours > 0 for d in PRODUCTION.downtimes)

    def test_numbers_are_unique_and_follow_the_posting_order(self):
        numbers = [d.downtime_number for d in PRODUCTION.downtimes]
        assert numbers == sorted(numbers) and len(set(numbers)) == len(numbers)


class TestMasterData:
    def test_every_company_has_three_work_centers_in_its_plant(self):
        assert len(WORK_CENTERS) == 3 * len(COMPANIES) and {w.company_code for w in WORK_CENTERS} == {c.code for c in COMPANIES}


class TestInTheDatabase:
    def count(self, db, table):
        return db.query(f"SELECT COUNT(*) AS n FROM {table}")[0]["n"]

    def test_the_story_seed_writes_the_production_tables(self):
        db = Database()
        prepare(db, "story", "august-contract", TODAY)
        assert self.count(db, "production_confirmation") == len(PRODUCTION.confirmations)
        assert self.count(db, "work_center_downtime") == len(PRODUCTION.downtimes)
        assert self.count(db, "work_center") == len(WORK_CENTERS)

    def test_values_come_back_exact(self):
        db = Database()
        prepare(db, "story", "august-contract", TODAY)
        row = db.query("SELECT * FROM production_confirmation WHERE confirmation_number = '8000000001'")[0]
        first = PRODUCTION.confirmations[0]
        assert quantity_from_minor(row["yield_quantity"]) == first.yield_quantity and from_minor(row["yield_value"]) == first.yield_value and from_minor(row["run_hours"]) == Decimal("8.00")

    def test_the_small_seed_has_no_shop_floor_but_has_work_centers(self):
        db = Database()
        prepare(db, "small", "august-contract", TODAY)
        assert self.count(db, "production_confirmation") == 0 and self.count(db, "work_center") == len(WORK_CENTERS)

    def test_an_older_database_is_rebuilt_and_keeps_api_orders(self):
        db = Database()
        prepare(db, "story", "august-contract", TODAY)
        db.execute("INSERT INTO sales_order VALUES ('0000099999', 'OR', '1', NULL, '2026-11-03', NULL, 'INR', 100, 'A', 'ME', '2026-11-03T09:00:00+00:00', '2026-11-03T09:00:00+00:00', 'INA1', 'IN', 'api')")
        db.execute("UPDATE meta SET value = '2' WHERE key = 'layout'")
        db.execute("DELETE FROM production_confirmation")
        assert prepare(db, "story", "august-contract", TODAY + timedelta(days=0)) is True
        assert self.count(db, "production_confirmation") == len(PRODUCTION.confirmations)
        assert db.query("SELECT COUNT(*) AS n FROM sales_order WHERE origin = 'api'")[0]["n"] == 1
