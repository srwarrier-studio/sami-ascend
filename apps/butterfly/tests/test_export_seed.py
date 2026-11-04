from datetime import date
from decimal import Decimal

from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.export_master import COUNTRY_NAMES
from butterfly.infrastructure.memory.export_seed import build_exports
from butterfly.infrastructure.memory.scenarios import find_scenario
from butterfly.infrastructure.memory.story_seed import build_story_seed
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.money import from_minor
from butterfly.infrastructure.sqlite.seeder import prepare

TODAY = date(2026, 11, 3)
STORY = build_story_seed(TODAY, find_scenario("august-contract"), COMPANIES)
SHIPMENTS = build_exports(STORY, TODAY)
ORDERS = {o.sales_order: o for o in STORY.orders}


def shipped(order):
    return order.requested_delivery_date or order.order_date


def export_orders():
    return [o for o in STORY.orders if o.overall_status != "X" and o.country != "IN" and shipped(o) <= TODAY]


class TestShipments:
    def test_there_is_one_shipment_for_every_export_order_shipped_up_to_today(self):
        assert sorted(s.sales_order for s in SHIPMENTS) == sorted(o.sales_order for o in export_orders())

    def test_cancelled_and_domestic_orders_have_no_shipment(self):
        numbers = {s.sales_order for s in SHIPMENTS}
        assert all(o.sales_order not in numbers for o in STORY.orders if o.overall_status == "X" or o.country == "IN")

    def test_nothing_ships_in_the_future(self):
        assert max(s.shipment_date for s in SHIPMENTS) <= TODAY
        assert all(s.shipment_date == shipped(ORDERS[s.sales_order]) for s in SHIPMENTS)

    def test_the_amounts_add_up_to_the_order_totals_in_rupees(self):
        expected = sum((o.total_net_amount * (80 if o.transaction_currency == "USD" else 1) for o in export_orders()), Decimal(0))
        assert abs(sum((s.net_amount for s in SHIPMENTS), Decimal(0)) - expected) < Decimal("0.01") * len(SHIPMENTS)
        assert {s.currency for s in SHIPMENTS} == {"INR"} and {s.document_currency for s in SHIPMENTS} == {"USD"}

    def test_a_shipment_carries_its_orders_customer_company_and_country(self):
        for s in SHIPMENTS:
            order = ORDERS[s.sales_order]
            assert (s.sold_to_party, s.company_code, s.country, s.customer_name, s.document_amount, s.document_currency) == (
                order.sold_to_party, order.company_code, order.country, order.customer_name, order.total_net_amount, order.transaction_currency,
            )
            assert s.country_name == COUNTRY_NAMES[s.country]

    def test_in_transit_exactly_when_the_arrival_is_after_today(self):
        for s in SHIPMENTS:
            if s.shipment_status == "T":
                assert s.actual_arrival_date is None and s.expected_arrival_date >= s.shipment_date
            else:
                assert s.shipment_status == "D" and s.shipment_date < s.actual_arrival_date <= TODAY
        assert any(s.shipment_status == "T" for s in SHIPMENTS) and any(s.shipment_status == "D" for s in SHIPMENTS)

    def test_transit_times_follow_the_mode(self):
        ranges = {"S": (18, 32), "A": (3, 6), "R": (4, 8)}
        for s in SHIPMENTS:
            low, high = ranges[s.transport_mode]
            assert low <= (s.expected_arrival_date - s.shipment_date).days <= high

    def test_about_three_in_five_go_by_sea_and_some_arrive_late(self):
        sea = sum(1 for s in SHIPMENTS if s.transport_mode == "S") / len(SHIPMENTS)
        assert 0.5 < sea < 0.7
        assert any(s.actual_arrival_date and s.actual_arrival_date > s.expected_arrival_date for s in SHIPMENTS)

    def test_numbers_are_unique_and_follow_the_shipping_order(self):
        numbers = [s.shipment for s in SHIPMENTS]
        assert numbers == sorted(numbers) and len(set(numbers)) == len(numbers)
        assert [s.shipment_date for s in SHIPMENTS] == sorted(s.shipment_date for s in SHIPMENTS)

    def test_the_same_seed_gives_the_same_shipments(self):
        assert build_exports(STORY, TODAY) == SHIPMENTS


class TestInTheDatabase:
    def count(self, db, table):
        return db.query(f"SELECT COUNT(*) AS n FROM {table}")[0]["n"]

    def test_the_story_seed_writes_the_shipments(self):
        db = Database()
        prepare(db, "story", "august-contract", TODAY)
        assert self.count(db, "export_shipment") == len(SHIPMENTS)
        row = db.query("SELECT * FROM export_shipment WHERE shipment = '6000000001'")[0]
        assert from_minor(row["net_amount"]) == SHIPMENTS[0].net_amount and row["actual_arrival_date"] == (SHIPMENTS[0].actual_arrival_date.isoformat() if SHIPMENTS[0].actual_arrival_date else None)

    def test_the_small_seed_has_no_shipments(self):
        db = Database()
        prepare(db, "small", "august-contract", TODAY)
        assert self.count(db, "export_shipment") == 0

    def test_an_older_database_is_rebuilt_and_keeps_api_orders(self):
        db = Database()
        prepare(db, "story", "august-contract", TODAY)
        db.execute("INSERT INTO sales_order (sales_order, sales_order_type, sold_to_party, customer_name, order_date, requested_delivery_date, transaction_currency, total_net_amount, overall_status, created_by_user, creation_date_time, last_change_date_time, company_code, country, origin, total_net_amount_local, local_currency) VALUES ('0000099999', 'OR', '1', NULL, '2026-11-03', NULL, 'INR', 100, 'A', 'ME', '2026-11-03T09:00:00+00:00', '2026-11-03T09:00:00+00:00', 'INA1', 'IN', 'api', 100, 'INR')")
        db.execute("UPDATE meta SET value = '3' WHERE key = 'layout'")
        db.execute("DELETE FROM export_shipment")
        assert prepare(db, "story", "august-contract", TODAY) is True
        assert self.count(db, "export_shipment") == len(SHIPMENTS)
        assert db.query("SELECT COUNT(*) AS n FROM sales_order WHERE origin = 'api'")[0]["n"] == 1
