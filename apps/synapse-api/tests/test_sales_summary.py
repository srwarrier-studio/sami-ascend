from datetime import date
from decimal import Decimal

import pytest
from test_routes_totals import make_client

from synapse_api.application.sales_summary import GetSalesSummary, money
from synapse_api.domain.entities.sales import CustomerSales, DailySales
from synapse_api.infrastructure.mock_sales_source import MockSalesSource

TODAY = date(2026, 11, 2)


def day(d: date, amount: str, currency: str = "INR") -> DailySales:
    return DailySales(d, Decimal(amount), 1, currency)


def customer(code: str, name: str, d: date, amount: str, currency: str = "INR") -> CustomerSales:
    return CustomerSales(code, name, d, Decimal(amount), 1, currency)


def summary(daily=(), customers=(), target: str = "1000000") -> list[str]:
    source = MockSalesSource(list(daily), customers=list(customers))
    return GetSalesSummary(source, Decimal(target)).execute(TODAY, "INR")


class TestMoney:
    @pytest.mark.parametrize(
        ("amount", "currency", "text"),
        [("353720", "INR", "₹3,53,720"), ("85224849", "INR", "₹8,52,24,849"), ("999", "INR", "₹999"), ("353720", "USD", "$353,720"), ("5", "GBP", "GBP 5")],
    )
    def test_writes_the_amount_the_way_the_currency_is_read(self, amount, currency, text):
        assert money(Decimal(amount), currency) == text


class TestHeadline:
    def test_names_the_days_and_says_it_is_early(self):
        lines = summary([day(TODAY, "353720"), day(date(2026, 10, 2), "848000")])
        assert lines[0] == "Sales this month are ₹3,53,720 (1–2 Nov, 2 of 30 days so far), down 58.3% on 1–2 Oct."

    def test_up_when_it_rose_and_no_note_late_in_the_month(self):
        late = date(2026, 11, 20)
        source = MockSalesSource([day(late, "300"), day(date(2026, 10, 5), "200")])
        line = GetSalesSummary(source, Decimal(0)).execute(late, "INR")[0]
        assert line == "Sales this month are ₹300 (1–20 Nov), up 50.0% on 1–20 Oct."

    def test_says_so_when_there_was_nothing_to_compare(self):
        assert "none on the same days last month" in summary([day(TODAY, "100")])[0]

    def test_nothing_at_all_gives_no_sentences(self):
        assert summary([], target="0") == []


class TestMover:
    def test_names_the_customer_with_the_biggest_change(self):
        lines = summary(
            [day(TODAY, "300"), day(date(2026, 10, 2), "100")],
            [customer("1", "Eastern Castings", TODAY, "250"), customer("2", "Bharat Steels", TODAY, "50"), customer("2", "Bharat Steels", date(2026, 10, 2), "100")],
        )
        assert lines[1] == "Eastern Castings moved most: ₹250 more than on 1–2 Oct."

    def test_a_customer_who_stopped_buying_counts_as_less(self):
        lines = summary([day(TODAY, "10"), day(date(2026, 10, 2), "500")], [customer("2", "Bharat Steels", date(2026, 10, 2), "500")])
        assert lines[1] == "Bharat Steels moved most: ₹500 less than on 1–2 Oct."

    def test_left_out_without_customers(self):
        assert len(summary([day(TODAY, "10")], target="0")) == 1


class TestTarget:
    def test_behind_the_pace(self):
        assert summary([day(TODAY, "10000")])[-1] == "1% of the ₹10,00,000 monthly target is reached with 7% of the month gone, so sales are behind the pace."

    def test_ahead_of_the_pace(self):
        assert summary([day(TODAY, "900000")])[-1].endswith("so sales are ahead of the pace.")

    def test_left_out_without_a_target(self):
        assert "target" not in " ".join(summary([day(TODAY, "10")], target="0"))


class TestRoute:
    BASE = "/v1/synapse/summary"

    def test_needs_a_signed_in_manager(self):
        source = MockSalesSource([])
        assert make_client(source).get(self.BASE).status_code == 401
        assert make_client(source, ["sales"]).get(self.BASE).status_code == 403

    def test_serves_the_sentences_with_the_time_and_currency(self):
        from test_routes_totals import DAILY

        body = make_client(MockSalesSource(DAILY), ["management"]).get(self.BASE + "?currency=INR").json()
        assert body["currency"] == "INR"
        assert body["sentences"][0].startswith("Sales this month are")
        assert body["asOf"].endswith("+00:00")

    def test_a_bad_currency_is_422(self):
        assert make_client(MockSalesSource([]), ["management"]).get(self.BASE + "?currency=US").status_code == 422
