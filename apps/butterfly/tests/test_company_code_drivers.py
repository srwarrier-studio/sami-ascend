from dataclasses import replace
from datetime import date

from butterfly.application.usecase.summarize_purchases_by_day import SummarizePurchasesByDay
from butterfly.application.usecase.summarize_purchases_by_material import SummarizePurchasesByMaterial
from butterfly.application.usecase.summarize_purchases_by_supplier import SummarizePurchasesBySupplier
from butterfly.application.usecase.summarize_receivables import SummarizeReceivables
from butterfly.application.usecase.summarize_receivables_ageing import SummarizeReceivablesAgeing
from butterfly.application.usecase.summarize_receivables_by_customer import SummarizeReceivablesByCustomer
from butterfly.infrastructure.api.odata import DRIVERS_ROOT
from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.in_memory_driver_repo import InMemoryDriverRepo
from butterfly.infrastructure.memory.story_seed import build_story_seed
from driver_data import make_driver_client

TODAY = date(2026, 10, 31)
SEED = build_story_seed(TODAY)
OPEN = next(i for i in SEED.invoices if i.clearing_date is None)
DELIVERY = SEED.deliveries[0]
OTHER_DELIVERY = replace(DELIVERY, company_code="INA2")
OTHER_INVOICE = replace(OPEN, invoice="9999999999", company_code="INA2")
REPO = InMemoryDriverRepo(deliveries=[DELIVERY, OTHER_DELIVERY], invoices=[OPEN, OTHER_INVOICE])


class TestInvoicesBelongToTheCompanyOfTheirOrder:
    def test_every_invoice_has_the_company_of_its_order(self):
        companies = {o.sales_order[1:]: o.company_code for o in SEED.orders}
        assert all(i.company_code == companies[i.invoice[1:]] for i in SEED.invoices)


class TestPurchaseSummariesKeepCompaniesApart:
    def test_each_summary_has_a_row_per_company(self):
        for use_case in (SummarizePurchasesByDay, SummarizePurchasesBySupplier, SummarizePurchasesByMaterial):
            assert sorted(r.company_code for r in use_case(REPO).execute()) == ["INA1", "INA2"]


class TestReceivablesKeepCompaniesApart:
    def test_each_summary_has_a_row_per_company(self):
        for use_case in (SummarizeReceivables, SummarizeReceivablesByCustomer):
            assert sorted(r.company_code for r in use_case(REPO).execute(TODAY)) == ["INA1", "INA2"]

    def test_ageing_has_a_row_per_company_and_bucket(self):
        rows = SummarizeReceivablesAgeing(REPO).execute(TODAY)
        assert {r.company_code for r in rows} == {"INA1", "INA2"} and len(rows) == 2


class TestReadingByCompany:
    def test_every_drivers_entity_filters_on_the_company_code(self):
        client = make_driver_client()
        for entity in ("SalesContract", "PurchaseDelivery", "ProductionOrder", "ProductionOrderComponent", "PurchaseSummaryByDay", "CustomerInvoice", "ReceivablesSummary"):
            body = client.get(DRIVERS_ROOT + entity + "?$filter=CompanyCode eq '9999'").json()
            assert body["value"] == [], entity


GROUP = build_story_seed(TODAY, companies=COMPANIES)
GROUP_REPO = InMemoryDriverRepo(invoices=GROUP.invoices)


class TestReceivablesOfEveryCompany:
    def test_every_company_has_open_and_overdue_invoices_in_its_own_currencies(self):
        for company in COMPANIES:
            currencies = {c.currency for c in company.customers}
            rows = [r for r in SummarizeReceivables(GROUP_REPO).execute(TODAY) if r.company_code == company.code]
            assert {r.currency for r in rows} == currencies
            assert all(r.open_amount > 0 and r.overdue_amount > 0 for r in rows)

    def test_the_customer_rows_of_a_company_add_up_to_its_summary(self):
        for summary in SummarizeReceivables(GROUP_REPO).execute(TODAY):
            parts = [r for r in SummarizeReceivablesByCustomer(GROUP_REPO).execute(TODAY) if (r.company_code, r.currency) == (summary.company_code, summary.currency)]
            assert sum(r.open_amount for r in parts) == summary.open_amount

    def test_ageing_of_a_company_adds_up_to_its_summary(self):
        for summary in SummarizeReceivables(GROUP_REPO).execute(TODAY):
            parts = [r for r in SummarizeReceivablesAgeing(GROUP_REPO).execute(TODAY) if (r.company_code, r.currency) == (summary.company_code, summary.currency)]
            assert sum(r.open_amount for r in parts) == summary.open_amount

    def test_customers_of_other_countries_pay_on_longer_terms_than_domestic_ones(self):
        terms = {c.customer_id: c.terms_days for company in COMPANIES for c in company.customers}
        domestic = [terms[c.customer_id] for company in COMPANIES for c in company.customers if c.country == "IN"]
        abroad = [terms[c.customer_id] for company in COMPANIES for c in company.customers if c.country != "IN"]
        assert sum(abroad) / len(abroad) > sum(domestic) / len(domestic)

    def test_the_customer_who_never_pays_is_in_the_story_company(self):
        never = [c for company in COMPANIES for c in company.customers if c.delay_days >= 1000]
        assert [c.customer_id for c in never] == ["0000100005"]
