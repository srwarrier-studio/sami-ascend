import json
import re
from datetime import date
from pathlib import Path
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from butterfly.entrypoint.app import build_default_app, create_app
from butterfly.infrastructure.api.odata import FINANCE_ROOT
from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.finance_seed import build_cash
from butterfly.infrastructure.memory.in_memory_finance_repo import InMemoryFinanceRepo as MemoryFinance
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo as MemoryOrders
from butterfly.infrastructure.memory.scenarios import find_scenario
from butterfly.infrastructure.memory.story_seed import build_story_seed
from butterfly.infrastructure.sqlite.finance_repo import SqliteFinanceRepo

TODAY = date(2026, 10, 31)
STORY = build_story_seed(TODAY, find_scenario("august-contract"), COMPANIES)
CASH = build_cash(STORY.invoices, STORY.deliveries, TODAY)
CONTRACT = (Path(__file__).resolve().parents[3] / "docs/sap/finance-contract.md").read_text()
EXAMPLES = re.findall(r"```\nGET \{root\}([^\n]+)\n```\n\n```json\n(.*?)\n```", CONTRACT, re.DOTALL)

MEMORY = TestClient(create_app(MemoryOrders([]), finance=MemoryFinance(CASH)))
SQLITE = TestClient(create_app(MemoryOrders([]), finance=SqliteFinanceRepo.from_payments(CASH)))


def get(client: TestClient, path: str):
    response = client.get(FINANCE_ROOT.rstrip("/") + "/" + quote(path, safe="/?=&$,()'"))
    return response.status_code, response.json()


QUERIES = [
    "CashPayment?$top=5",
    "CashPayment?$filter=PaymentType eq 'C' and Amount gt 100000.5&$orderby=Amount desc,PaymentDocument&$top=6&$count=true",
    "CashPayment?$filter=DocumentCurrency eq 'USD' and PostingDate ge 2026-10-01&$orderby=PostingDate desc,PaymentDocument&$top=5&$count=true",
    "CashPayment?$filter=contains(PartnerName,'Trading') or ExpenseCategory eq 'RENT'&$count=true&$top=4",
    "CashPayment?$filter=not (Direction eq 'O')&$count=true&$top=1",
    "CashPayment?$select=PaymentDocument,Amount&$orderby=PaymentDocument desc&$skip=10&$top=4",
    "CashSummaryByDay?$filter=PostingDate ge 2026-10-01&$orderby=PostingDate,Direction,CompanyCode&$count=true&$top=40",
    "CashSummaryByDay?$filter=Direction eq 'O' and Amount gt 1000000.5&$orderby=Amount desc&$top=5&$count=true",
    "ExpenseSummaryByDay?$filter=PostingDate ge 2026-10-01 and CompanyCode eq 'INA2'&$orderby=PostingDate,ExpenseCategory&$count=true&$top=40",
    "ExpenseSummaryByDay?$filter=ExpenseCategory eq 'SALARIES'&$orderby=PostingDate desc,CompanyCode&$top=6&$count=true",
]


@pytest.mark.parametrize("path", QUERIES)
def test_the_database_answers_like_the_lists(path):
    status, body = get(SQLITE, path)
    assert status == 200 and (status, body) == get(MEMORY, path)


@pytest.mark.parametrize("path", ["CashPayment?$filter=Bogus eq 'x'", "CashSummaryByDay?$orderby=Nope", "CashPayment?$top=abc", "ExpenseSummaryByDay?$filter=PostingDate eq 'x'"])
def test_a_bad_query_is_refused_the_same_way(path):
    assert get(SQLITE, path) == get(MEMORY, path) and get(SQLITE, path)[0] == 400


class TestRows:
    def test_a_payment_has_exactly_the_contract_fields_in_order(self):
        row = get(SQLITE, "CashPayment?$top=1")[1]["value"][0]
        assert list(row) == [
            "PaymentDocument", "PostingDate", "Direction", "PaymentType", "Partner", "PartnerName", "ExpenseCategory", "Reference", "Amount", "Currency", "DocumentAmount", "DocumentCurrency",
            "CompanyCode",
        ]


class TestSummaryTotals:
    def test_cash_by_day_adds_up_to_the_payments(self):
        rows = get(SQLITE, "CashSummaryByDay?$top=1000&$filter=PostingDate eq 2026-10-30")[1]["value"]
        for direction in "IO":
            expected = sum(p.amount for p in CASH if p.posting_date == date(2026, 10, 30) and p.direction == direction)
            assert sum(float(r["Amount"]) for r in rows if r["Direction"] == direction) == pytest.approx(float(expected))

    def test_expenses_by_day_hold_only_running_costs(self):
        rows = get(SQLITE, "ExpenseSummaryByDay?$top=1000&$filter=PostingDate eq 2026-10-25")[1]["value"]
        assert {r["ExpenseCategory"] for r in rows} == {"SALARIES"} and len(rows) == 3


class TestContractExamples:
    def test_the_contract_has_an_example_for_every_entity(self):
        assert len(EXAMPLES) == 3

    @pytest.mark.parametrize("request_text,response_text", EXAMPLES, ids=[e[0][:50] for e in EXAMPLES])
    def test_the_data_gives_exactly_the_example(self, request_text, response_text):
        for client in (MEMORY, SQLITE):
            response = client.get(FINANCE_ROOT + request_text)
            assert response.status_code == 200
            assert response.json() == json.loads(response_text)


class TestRunner:
    def test_the_story_seed_serves_payments_and_the_small_seed_none(self, tmp_path):
        story = TestClient(build_default_app(TODAY, "story", "august-contract", str(tmp_path / "a.db")))
        small = TestClient(build_default_app(TODAY, "small", "august-contract", str(tmp_path / "b.db")))
        assert story.get(FINANCE_ROOT + "CashPayment?$count=true&$top=1").json()["@odata.count"] == len(CASH)
        assert small.get(FINANCE_ROOT + "CashPayment?$count=true&$top=1").json()["@odata.count"] == 0
