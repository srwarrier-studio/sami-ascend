from dataclasses import replace

from butterfly.application.usecase.summarize_by_customer import SummarizeByCustomer
from butterfly.application.usecase.summarize_by_day import SummarizeByDay
from butterfly.application.usecase.summarize_by_material import SummarizeByMaterial
from butterfly.infrastructure.api.odata import ROOT
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo
from conftest import ORDERS, make_client

SECOND = replace(next(o for o in ORDERS if o.overall_status != "X"), company_code="2000")
TWO_COMPANIES = InMemorySalesOrderRepo([*ORDERS, SECOND])


class TestSummariesKeepCompaniesApart:
    def test_the_same_day_has_a_row_per_company(self):
        rows = [r for r in SummarizeByDay(TWO_COMPANIES).execute() if r.order_date == SECOND.order_date]
        assert sorted(r.company_code for r in rows) == ["1000", "2000"]

    def test_the_second_company_row_holds_only_its_order(self):
        row = next(r for r in SummarizeByDay(TWO_COMPANIES).execute() if r.company_code == "2000")
        assert (row.total_net_amount, row.order_count) == (SECOND.total_net_amount, 1)

    def test_customer_and_material_summaries_split_by_company_too(self):
        assert {r.company_code for r in SummarizeByCustomer(TWO_COMPANIES).execute()} == {"1000", "2000"}
        assert {r.company_code for r in SummarizeByMaterial(TWO_COMPANIES).execute()} == {"1000", "2000"}


class TestReadingByCompany:
    def test_orders_filter_on_the_company_code(self):
        client = make_client([*ORDERS, SECOND])
        rows = client.get(ROOT + "SalesOrder", params={"$filter": "CompanyCode eq '2000'"}).json()["value"]
        assert [r["SalesOrder"] for r in rows] == [SECOND.sales_order]

    def test_summaries_filter_on_the_company_code(self):
        client = make_client([*ORDERS, SECOND])
        rows = client.get(ROOT + "SalesSummaryByDay", params={"$filter": "CompanyCode eq '2000'"}).json()["value"]
        assert [r["CompanyCode"] for r in rows] == ["2000"]
