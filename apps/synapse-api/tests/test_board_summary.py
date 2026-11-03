from datetime import date
from decimal import Decimal

import pytest
from test_routes_totals import SECRET, make_client, token_with
from fastapi.testclient import TestClient
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from synapse_api.application.board_summary import GetBoardSummary
from synapse_api.domain.entities.purchases import DailyPurchases, PurchaseItem, SupplierPurchases
from synapse_api.domain.entities.receivables import AgeBucket, CustomerReceivable, ReceivablesTotal
from synapse_api.domain.entities.sales import CustomerSales, DailySales
from synapse_api.entrypoint.app import create_app
from synapse_api.infrastructure.mock_purchase_source import MockPurchaseSource
from synapse_api.infrastructure.mock_receivables_source import MockReceivablesSource
from synapse_api.infrastructure.mock_sales_source import MockSalesSource
from synapse_api.infrastructure.settings import Settings

TODAY = date(2026, 10, 27)
LAST = date(2026, 9, 2)
NOW = date(2026, 10, 2)


def sales() -> MockSalesSource:
    return MockSalesSource([DailySales(NOW, Decimal("300"), 1, "INR"), DailySales(LAST, Decimal("200"), 1, "INR")], customers=[CustomerSales("1", "Eastern", NOW, Decimal("300"), 1, "INR")])


def purchases() -> MockPurchaseSource:
    return MockPurchaseSource(
        daily=[DailyPurchases(NOW, Decimal("1000"), 2, "INR"), DailyPurchases(LAST, Decimal("500"), 1, "INR")],
        suppliers=[SupplierPurchases("1", "Pack-Rite", NOW, Decimal("750"), 1, "INR"), SupplierPurchases("2", "Malnad", NOW, Decimal("250"), 1, "INR")],
        items=[
            PurchaseItem("1", "00010", "Pack-Rite", date(2026, 9, 1), date(2026, 10, 1), date(2026, 10, 1), Decimal("5"), "INR", "D"),
            PurchaseItem("2", "00010", "Malnad", date(2026, 9, 1), date(2026, 10, 2), date(2026, 10, 9), Decimal("5"), "INR", "D"),
            PurchaseItem("3", "00010", "Malnad", date(2026, 10, 1), date(2026, 11, 20), None, Decimal("5"), "INR", "O"),
        ],
    )


def receivables() -> MockReceivablesSource:
    return MockReceivablesSource(
        totals=[ReceivablesTotal("INR", Decimal("1000"), Decimal("250"), 4, 1)],
        customers=[CustomerReceivable("1", "Kestrel", "INR", Decimal("600"), Decimal("200")), CustomerReceivable("2", "Alder", "INR", Decimal("400"), Decimal("50"))],
        buckets=[AgeBucket("current", "INR", Decimal("750"), 3), AgeBucket("31-60", "INR", Decimal("150"), 1), AgeBucket("90+", "INR", Decimal("100"), 1)],
    )


def board(*ids: str, target: str = "1000", **sources) -> list[str]:
    return GetBoardSummary(sales(), Decimal(target), **sources).execute(TODAY, "INR", set(ids))


class TestSales:
    def test_a_sales_card_gives_the_headline_only(self):
        assert board("sales-month") == ["Sales this month are ₹300 (1–27 Oct), up 50.0% on 1–27 Sep."]

    def test_a_target_widget_adds_the_pace_first_and_the_customer_widget_the_mover(self):
        lines = board("sales-month", "month-target", "top-customers")
        assert len(lines) == 2 and "monthly target" in lines[1]
        assert "moved most" in board("sales-month", "top-customers")[1]


class TestTopics:
    def test_a_board_with_three_topics_gets_each_in_order(self):
        lines = board("fin-receivables", "pur-ontime", "sales-month", purchases=purchases(), receivables=receivables())
        assert lines[0].startswith("Sales this month")
        assert lines[1].startswith("Purchases this month")
        assert lines[2].startswith("50% of purchase items due in the last 90 days")
        assert lines[3] == "₹1,000 is outstanding from customers, ₹250 (25%) of it past its due date."
        assert len(lines) == 4

    def test_each_topic_has_at_most_two_sentences(self):
        lines = board("pur-spend", "pur-ontime", "pur-open", "pur-vendors", purchases=purchases())
        assert len(lines) == 2

    def test_a_widget_licenses_only_its_own_sentence(self):
        assert [line for line in board("pur-spend", "pur-open", purchases=purchases())][1] == "1 purchase item is still open."
        assert "Pack-Rite is the biggest supplier this month: ₹750 (75% of purchases)." == board("pur-vendors", "pur-spend", purchases=purchases())[1]

    def test_receivables_sentences(self):
        lines = board("fin-overdue", "fin-ageing", receivables=receivables())
        assert lines[1] == "Kestrel has the most overdue: ₹200."
        assert board("fin-ageing", receivables=receivables())[1] == "₹250 is more than 30 days past due."

    def test_widgets_that_are_still_mock_say_nothing(self):
        assert board("inv-value", "exp-revenue", purchases=purchases(), receivables=receivables()) == []

    def test_no_widgets_says_nothing(self):
        assert board() == []

    def test_a_topic_without_a_source_is_skipped(self):
        assert len(board("sales-month", "pur-spend", "fin-receivables")) == 1


class TestPurchasesEarlyInTheMonth:
    def test_says_nothing_was_ordered_yet_and_gives_last_months_total(self):
        today = date(2026, 11, 3)
        source = MockPurchaseSource(daily=[DailyPurchases(date(2026, 10, 24), Decimal("17729000"), 6, "INR")])
        line = GetBoardSummary(MockSalesSource(), Decimal(0), purchases=source).execute(today, "INR", {"pur-spend"})
        assert line == ["No purchase orders raised yet this month; last month's total was ₹1,77,29,000."]

    def test_nothing_this_month_or_last_says_nothing(self):
        assert GetBoardSummary(MockSalesSource(), Decimal(0), purchases=MockPurchaseSource()).execute(TODAY, "INR", {"pur-spend"}) == []


class TestRoute:
    BASE = "/v1/synapse/summary"

    def client(self):
        app = create_app(sales(), Settings(jwt_secret=SECRET, _env_file=None), lambda: TODAY, purchases=purchases(), receivables=receivables())
        client = TestClient(app)
        client.cookies.set(ACCESS_TOKEN_COOKIE, token_with(["management"]))
        return client

    def test_the_sentences_follow_the_widgets_asked_for(self):
        client = self.client()
        only_sales = client.get(self.BASE + "?currency=INR&widgets=sales-month").json()["sentences"]
        three = client.get(self.BASE + "?currency=INR&widgets=sales-month,pur-spend,fin-receivables").json()["sentences"]
        assert len(only_sales) == 1 and len(three) == 3

    def test_no_widgets_or_unknown_ones_give_nothing(self):
        client = self.client()
        assert client.get(self.BASE).json()["sentences"] == []
        assert client.get(self.BASE + "?widgets=nope,inv-value").json()["sentences"] == []

    def test_the_order_of_the_ids_does_not_matter(self):
        client = self.client()
        first = client.get(self.BASE + "?widgets=sales-month,pur-spend").json()
        assert client.get(self.BASE + "?widgets=pur-spend,sales-month").json() == first

    def test_too_many_widgets_is_422(self):
        ids = ",".join(f"w{n}" for n in range(31))
        assert self.client().get(self.BASE + f"?widgets={ids}").status_code == 422
