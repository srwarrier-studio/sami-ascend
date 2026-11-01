from datetime import date, datetime, timezone
from decimal import Decimal

from fastapi.testclient import TestClient

from butterfly.application.usecase.summarize_receivables import SummarizeReceivables
from butterfly.application.usecase.summarize_receivables_ageing import SummarizeReceivablesAgeing
from butterfly.application.usecase.summarize_receivables_by_customer import SummarizeReceivablesByCustomer
from butterfly.domain.entities.drivers import CustomerInvoice
from butterfly.entrypoint.app import build_default_app
from butterfly.infrastructure.api.odata import DRIVERS_ROOT
from butterfly.infrastructure.memory.in_memory_driver_repo import InMemoryDriverRepo
from butterfly.infrastructure.memory.story_seed import build_story_seed

TODAY = date(2026, 10, 31)
SEED = build_story_seed(TODAY)
REPO = InMemoryDriverRepo(invoices=SEED.invoices)


def invoice(number, amount, invoice_date, due, cleared=None, currency="INR", customer="0000100001"):
    return CustomerInvoice(number, customer, "Harborline", invoice_date, due, Decimal(amount), currency, Decimal(amount) if cleared else Decimal("0.00"), cleared)


def repo_of(*invoices):
    return InMemoryDriverRepo(invoices=list(invoices))


class TestOneDay:
    def test_open_and_overdue_are_split_by_the_due_date(self):
        repo = repo_of(invoice("1", "100.00", date(2026, 9, 1), date(2026, 10, 1)), invoice("2", "50.00", date(2026, 10, 20), date(2026, 11, 20)))
        row = SummarizeReceivables(repo).execute(date(2026, 10, 31))[0]
        assert (row.open_amount, row.overdue_amount, row.open_count, row.overdue_count) == (Decimal("150.00"), Decimal("100.00"), 2, 1)

    def test_an_invoice_due_on_the_day_is_not_yet_overdue(self):
        repo = repo_of(invoice("1", "100.00", date(2026, 9, 1), date(2026, 10, 31)))
        assert SummarizeReceivables(repo).execute(date(2026, 10, 31))[0].overdue_amount == Decimal("0.00")

    def test_a_cleared_invoice_is_left_out(self):
        repo = repo_of(invoice("1", "100.00", date(2026, 9, 1), date(2026, 10, 1), cleared=date(2026, 10, 5)))
        assert SummarizeReceivables(repo).execute(date(2026, 10, 31)) == []

    def test_each_currency_has_its_own_row(self):
        repo = repo_of(invoice("1", "100.00", date(2026, 9, 1), date(2026, 10, 1)), invoice("2", "7.00", date(2026, 9, 1), date(2026, 10, 1), currency="USD"))
        assert [(r.currency, r.open_amount) for r in SummarizeReceivables(repo).execute(date(2026, 10, 31))] == [("INR", Decimal("100.00")), ("USD", Decimal("7.00"))]


class TestAnEarlierDay:
    repo = repo_of(invoice("1", "100.00", date(2026, 9, 1), date(2026, 10, 1), cleared=date(2026, 10, 20)), invoice("2", "50.00", date(2026, 10, 25), date(2026, 11, 25)))

    def test_a_later_clearing_is_not_known_yet(self):
        row = SummarizeReceivables(self.repo).execute(date(2026, 10, 10))[0]
        assert (row.open_amount, row.overdue_amount) == (Decimal("100.00"), Decimal("100.00"))

    def test_a_later_invoice_does_not_exist_yet(self):
        assert SummarizeReceivables(self.repo).execute(date(2026, 10, 10))[0].open_count == 1

    def test_the_row_carries_the_day(self):
        assert SummarizeReceivables(self.repo).execute(date(2026, 10, 10))[0].as_of_date == date(2026, 10, 10)


class TestAgeing:
    def test_buckets_follow_the_days_past_due(self):
        due = {"a": date(2026, 11, 5), "b": date(2026, 10, 15), "c": date(2026, 9, 15), "d": date(2026, 8, 15), "e": date(2026, 6, 1)}
        repo = repo_of(*(invoice(key, "10.00", date(2026, 5, 1), day) for key, day in due.items()))
        rows = SummarizeReceivablesAgeing(repo).execute(date(2026, 10, 31))
        assert [r.age_bucket for r in rows] == ["current", "1-30", "31-60", "61-90", "90+"]

    def test_the_boundary_days_fall_in_the_lower_bucket(self):
        repo = repo_of(invoice("1", "10.00", date(2026, 5, 1), date(2026, 10, 1)), invoice("2", "10.00", date(2026, 5, 1), date(2026, 9, 1)))
        assert [r.age_bucket for r in SummarizeReceivablesAgeing(repo).execute(date(2026, 10, 31))] == ["1-30", "31-60"]

    def test_every_bucket_has_data_in_the_default_story(self):
        assert [r.age_bucket for r in SummarizeReceivablesAgeing(REPO).execute(TODAY)] == ["current", "1-30", "31-60", "61-90", "90+"]


class TestStoryTotalsAgree:
    def test_customers_and_ageing_add_up_to_the_summary(self):
        summary = SummarizeReceivables(REPO).execute(TODAY)[0]
        assert sum(r.open_amount for r in SummarizeReceivablesByCustomer(REPO).execute(TODAY)) == summary.open_amount
        assert sum(r.overdue_amount for r in SummarizeReceivablesByCustomer(REPO).execute(TODAY)) == summary.overdue_amount
        assert sum(r.open_amount for r in SummarizeReceivablesAgeing(REPO).execute(TODAY)) == summary.open_amount

    def test_the_overdue_amount_is_everything_past_current(self):
        summary = SummarizeReceivables(REPO).execute(TODAY)[0]
        assert sum(r.open_amount for r in SummarizeReceivablesAgeing(REPO).execute(TODAY) if r.age_bucket != "current") == summary.overdue_amount

    def test_customers_come_in_customer_order_and_leave_out_those_with_nothing_open(self):
        rows = SummarizeReceivablesByCustomer(REPO).execute(TODAY)
        assert [r.sold_to_party for r in rows] == sorted(r.sold_to_party for r in rows)
        assert all(r.open_amount > 0 for r in rows)

    def test_the_customer_who_never_pays_owes_the_most(self):
        rows = SummarizeReceivablesByCustomer(REPO).execute(TODAY)
        assert max(rows, key=lambda r: r.open_amount).sold_to_party == "0000100005"


class TestRoutes:
    client = TestClient(build_default_app(TODAY))

    def get(self, path):
        return self.client.get(DRIVERS_ROOT + path)

    def test_the_ageing_route_reads_the_day_from_as_of_date(self):
        body = self.get("ReceivablesAgeing?AsOfDate=2026-10-10").json()
        assert {row["AsOfDate"] for row in body["value"]} == {"2026-10-10"}
        assert body["@odata.context"] == "$metadata#ReceivablesAgeing"

    def test_without_a_day_the_summary_is_for_today(self):
        assert self.get("ReceivablesSummary").json()["value"][0]["AsOfDate"] == datetime.now(timezone.utc).date().isoformat()

    def test_a_bad_day_is_a_bad_request(self):
        response = self.get("ReceivablesSummary?AsOfDate=yesterday")
        assert response.status_code == 400
        assert response.json()["error"]["target"] == "AsOfDate"

    def test_filter_orderby_top_and_count_work(self):
        body = self.get("ReceivablesByCustomer?AsOfDate=2026-10-31&$filter=OpenAmount gt 0&$orderby=OpenAmount desc&$top=2&$count=true").json()
        assert len(body["value"]) == 2 and body["@odata.count"] >= 2
        assert Decimal(body["value"][0]["OpenAmount"]) >= Decimal(body["value"][1]["OpenAmount"])
