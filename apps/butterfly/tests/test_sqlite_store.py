from datetime import date, timedelta
from decimal import Decimal

import pytest

from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.scenarios import find_scenario
from butterfly.infrastructure.memory.seed import build_seed
from butterfly.infrastructure.memory.story_seed import build_story_seed
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.money import from_minor, quantity_from_minor, quantity_to_minor, to_minor
from butterfly.infrastructure.sqlite.seeder import prepare

TODAY = date(2026, 11, 3)


def count(db: Database, table: str, where: str = "1 = 1") -> int:
    return db.query(f"SELECT COUNT(*) AS n FROM {table} WHERE {where}")[0]["n"]


class TestMoney:
    def test_keeps_money_exact_in_cents(self):
        assert to_minor(Decimal("1250.05")) == 125005
        assert from_minor(125005) == Decimal("1250.05")

    def test_keeps_quantities_in_thousandths(self):
        assert quantity_to_minor(Decimal("5000.250")) == 5000250
        assert quantity_from_minor(5000250) == Decimal("5000.250")

    def test_refuses_more_decimals_than_the_store_keeps(self):
        with pytest.raises(ValueError):
            to_minor(Decimal("1.005"))

    def test_zero_and_negative_round_trip(self):
        assert from_minor(to_minor(Decimal("0.00"))) == Decimal("0.00")
        assert from_minor(to_minor(Decimal("-12.50"))) == Decimal("-12.50")


class TestSchema:
    def test_creates_every_table(self):
        names = {row["name"] for row in Database().query("SELECT name FROM sqlite_master WHERE type = 'table'")}
        assert {"sales_order", "sales_order_item", "sales_contract", "purchase_delivery", "customer_invoice", "production_order", "production_order_component", "customer", "material", "company", "meta"} <= names

    def test_an_item_needs_its_order(self):
        with pytest.raises(Exception):
            Database().execute("INSERT INTO sales_order_item VALUES ('1', '10', 'M', NULL, 1000, 'KG', 100)")

    def test_a_failed_transaction_leaves_nothing(self):
        db = Database()
        with pytest.raises(RuntimeError):
            with db.transaction():
                db.execute("INSERT INTO company VALUES ('A', 'a')")
                raise RuntimeError("stop")
        assert count(db, "company") == 0


class TestSmallSeed:
    def test_writes_the_orders_with_their_items_and_the_master_data(self):
        db = Database()
        assert prepare(db, "small", "august-contract", TODAY) is True
        expected = build_seed(TODAY)
        assert count(db, "sales_order") == len(expected)
        assert count(db, "sales_order_item") == sum(len(o.items) for o in expected)
        assert count(db, "customer") == sum(len(c.customers) for c in COMPANIES)
        assert count(db, "sales_contract") == 0

    def test_totals_are_exact(self):
        db = Database()
        prepare(db, "small", "august-contract", TODAY)
        stored = from_minor(db.query("SELECT SUM(total_net_amount) AS s FROM sales_order")[0]["s"])
        assert stored == sum((o.total_net_amount for o in build_seed(TODAY)), Decimal("0.00"))


class TestStorySeed:
    def test_writes_every_entity_of_the_story(self):
        db = Database()
        prepare(db, "story", "august-contract", TODAY)
        story = build_story_seed(TODAY, find_scenario("august-contract"), COMPANIES)
        assert count(db, "sales_order") == len(story.orders)
        assert count(db, "sales_order_item") == sum(len(o.items) for o in story.orders)
        assert count(db, "sales_contract") == len(story.contracts)
        assert count(db, "purchase_delivery") == len(story.deliveries)
        assert count(db, "customer_invoice") == len(story.invoices)
        assert count(db, "production_order") == len(story.production_orders)
        assert count(db, "production_order_component") == len(story.components)

    def test_open_deliveries_keep_their_empty_actual_date(self):
        db = Database()
        prepare(db, "story", "august-contract", TODAY)
        open_rows = count(db, "purchase_delivery", "delivery_status = 'O' AND actual_delivery_date IS NULL")
        assert open_rows == count(db, "purchase_delivery", "delivery_status = 'O'") > 0


class TestKeepingAndRebuilding:
    def test_the_same_settings_on_the_same_day_keep_the_data(self, tmp_path):
        path = str(tmp_path / "butterfly.db")
        first = Database(path)
        assert prepare(first, "small", "august-contract", TODAY) is True
        first.execute("INSERT INTO sales_order VALUES ('0000099999', 'OR', '1', NULL, '2026-11-03', NULL, 'INR', 100, 'A', 'ME', '2026-11-03T09:00:00+00:00', '2026-11-03T09:00:00+00:00', 'INA1', 'IN', 'api')")
        first.close()
        second = Database(path)
        assert prepare(second, "small", "august-contract", TODAY) is False
        assert count(second, "sales_order", "origin = 'api'") == 1
        assert count(second, "sales_order") == len(build_seed(TODAY)) + 1

    def test_another_seed_rebuilds_the_seeded_data(self):
        db = Database()
        prepare(db, "small", "august-contract", TODAY)
        assert prepare(db, "story", "august-contract", TODAY) is True
        assert count(db, "sales_contract") > 0
        assert count(db, "sales_order") > len(build_seed(TODAY))

    def test_another_scenario_rebuilds(self):
        db = Database()
        prepare(db, "story", "august-contract", TODAY)
        before = count(db, "sales_contract")
        assert prepare(db, "story", "price-cut", TODAY) is True
        assert before > 0

    def test_a_new_day_moves_the_seed_but_keeps_orders_written_through_the_api(self):
        db = Database()
        prepare(db, "small", "august-contract", TODAY)
        db.execute("INSERT INTO sales_order VALUES ('0000099999', 'OR', '1', NULL, '2026-11-03', NULL, 'INR', 100, 'A', 'ME', '2026-11-03T09:00:00+00:00', '2026-11-03T09:00:00+00:00', 'INA1', 'IN', 'api')")
        assert prepare(db, "small", "august-contract", TODAY + timedelta(days=1)) is True
        assert count(db, "sales_order", "origin = 'api'") == 1
        assert count(db, "sales_order", "origin = 'seed'") == len(build_seed(TODAY))
        assert db.query("SELECT MAX(order_date) AS d FROM sales_order WHERE origin = 'seed'")[0]["d"] == (TODAY + timedelta(days=1)).isoformat()

    def test_an_unknown_seed_is_refused(self):
        with pytest.raises(ValueError):
            prepare(Database(), "huge", "august-contract", TODAY)
