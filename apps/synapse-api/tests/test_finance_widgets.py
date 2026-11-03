from datetime import date
from decimal import Decimal
from urllib.parse import unquote

import httpx
import pytest

from synapse_api.application.catalog import GetWidgetData, ListCatalog
from synapse_api.application.finance_summary import GetFinanceSummary
from synapse_api.application.finance_widgets import finance_catalog
from synapse_api.domain.entities.finance import CashDay, ExpenseDay, IncomingPayment
from synapse_api.infrastructure.butterfly_finance_source import ButterflyFinanceSource
from synapse_api.infrastructure.mock_finance_source import MockFinanceSource
from synapse_api.infrastructure.odata_reader import ODataReader

TODAY = date(2026, 10, 27)
TARGET = Decimal(1000)


def data(source: MockFinanceSource, entry_id: str, today: date = TODAY) -> dict:
    return GetWidgetData(finance_catalog(source, TARGET)).execute(entry_id, today, "INR", 5)


def cash(d: date, direction: str, amount: str) -> CashDay:
    return CashDay(d, direction, 1, Decimal(amount))


class TestList:
    def test_lists_the_five_cash_widgets_under_their_old_ids(self):
        entries = ListCatalog(finance_catalog(MockFinanceSource(), TARGET)).execute()
        assert [e.id for e in entries] == ["fin-collections", "fin-collection-target", "fin-cashflow", "fin-payments", "fin-expenses"]
        assert {e.category for e in entries} == {"Finance"}


class TestCollections:
    def source(self):
        return MockFinanceSource(cash=[cash(date(2026, 10, 2), "I", "300"), cash(date(2026, 10, 3), "O", "999"), cash(date(2026, 9, 2), "I", "200"), cash(date(2026, 9, 29), "I", "999")])

    def test_compares_incoming_with_the_same_days_last_month(self):
        props = data(self.source(), "fin-collections")
        assert props["value"] == 300.0 and props["delta"] == pytest.approx(0.5)
        assert props["caption"] == "1–27 Oct vs 1–27 Sep" and props["measure"] == "collections"
        assert len(props["trend"]) == 6 and props["trend"][-1] == 300.0

    def test_early_in_the_month_it_says_how_many_days_it_has(self):
        props = data(self.source(), "fin-collections", date(2026, 10, 3))
        assert props["note"] == "3 of 31 days so far" and props["partial"] is True

    def test_the_gauge_counts_incoming_against_the_target(self):
        props = data(self.source(), "fin-collection-target")
        assert (props["value"], props["target"]) == (300.0, 1000.0)


class TestCashflow:
    def test_has_six_months_of_cash_in_and_cash_out(self):
        source = MockFinanceSource(cash=[cash(date(2026, 10, 2), "I", "70"), cash(date(2026, 10, 3), "O", "40"), cash(date(2026, 5, 3), "O", "5")])
        props = data(source, "fin-cashflow")
        assert [p["label"] for p in props["data"]] == ["May", "Jun", "Jul", "Aug", "Sep", "Oct"]
        assert props["data"][-1]["value"] == 70.0 and props["compare"][-1]["value"] == 40.0 and props["compare"][0]["value"] == 5.0
        assert (props["label"], props["compareLabel"]) == ("Cash in", "Cash out")


class TestPaymentsAndExpenses:
    def test_payments_are_the_latest_received_first(self):
        payments = [IncomingPayment("1", date(2026, 10, 1), "Northwind", Decimal("10")), IncomingPayment("2", date(2026, 10, 5), "Harbor", Decimal("20"))]
        rows = data(MockFinanceSource(payments=payments), "fin-payments")["rows"]
        assert rows == [
            {"payment": "2", "customer": "Harbor", "date": "Mon 5 Oct", "amount": 20.0},
            {"payment": "1", "customer": "Northwind", "date": "Thu 1 Oct", "amount": 10.0},
        ]

    def test_expenses_are_named_ranked_and_old_ones_left_out(self):
        rows = [ExpenseDay(date(2026, 10, 1), "RENT", 1, Decimal("30")), ExpenseDay(date(2026, 10, 25), "SALARIES", 1, Decimal("90")), ExpenseDay(date(2026, 1, 1), "FREIGHT", 1, Decimal("999"))]
        assert data(MockFinanceSource(expenses=rows), "fin-expenses")["slices"] == [{"label": "Salaries", "value": 90.0}, {"label": "Rent", "value": 30.0}]


class TestOverview:
    def source(self):
        return MockFinanceSource(
            cash=[cash(date(2026, 10, 2), "I", "300"), cash(date(2026, 10, 3), "O", "100"), cash(date(2026, 9, 2), "I", "200")],
            expenses=[ExpenseDay(date(2026, 10, 25), "SALARIES", 1, Decimal("90")), ExpenseDay(date(2026, 10, 1), "RENT", 1, Decimal("10"))],
        )

    def test_names_the_headline_and_what_the_widgets_show(self):
        lines = GetFinanceSummary(self.source(), TARGET).execute(TODAY, "INR", {"fin-collection-target", "fin-cashflow", "fin-expenses"})
        assert lines[0] == "Collections this month are ₹300 (1–27 Oct), up 50.0% on 1–27 Sep."
        assert lines[1] == "Collections are 30% of the ₹1,000 monthly target."
        assert "₹200 more in than out" in lines[2]
        assert lines[3].startswith("Salaries is the largest running cost over the last 90 days: ₹90 (90% of costs)")

    def test_says_nothing_without_money(self):
        assert GetFinanceSummary(MockFinanceSource(), TARGET).execute(TODAY, "INR", {"fin-cashflow", "fin-expenses"}) == []


class TestButterflySource:
    def source(self, rows, urls):
        def handler(request):
            urls.append(unquote(str(request.url)))
            return httpx.Response(200, json={"value": rows})

        return ButterflyFinanceSource(ODataReader("http://sap/finance/", 5, httpx.MockTransport(handler)))

    def test_the_summaries_ask_for_the_range_and_company(self):
        urls = []
        start, end = date(2026, 10, 1), date(2026, 10, 31)
        cash_row = {"PostingDate": "2026-10-02", "Direction": "I", "PaymentCount": 2, "Amount": "400.00"}
        result = self.source([cash_row], urls).for_companies(("INA1",)).cash_days(start, end)
        assert (result[0].direction, result[0].count, result[0].amount) == ("I", 2, Decimal("400.00"))
        assert "CashSummaryByDay?$filter=PostingDate ge 2026-10-01 and PostingDate le 2026-10-31 and (CompanyCode eq 'INA1')&$orderby=PostingDate,Direction,Currency,CompanyCode" in urls[0]
        expense_row = {"PostingDate": "2026-10-01", "ExpenseCategory": "RENT", "PaymentCount": 1, "Amount": "9.00"}
        assert self.source([expense_row], urls).expense_days(start, end)[0].category == "RENT"
        assert "ExpenseSummaryByDay?" in urls[1]

    def test_incoming_payments_are_read_latest_first(self):
        urls = []
        row = {"PaymentDocument": "1500000001", "PostingDate": "2026-10-30", "PartnerName": "Harbor", "Partner": "1", "Amount": "5.00"}
        payments = self.source([row], urls).incoming_payments(5)
        assert (payments[0].customer, payments[0].day) == ("Harbor", date(2026, 10, 30))
        assert "CashPayment?$filter=Direction eq 'I'&$orderby=PostingDate desc,PaymentDocument desc&$top=5" in urls[0]
