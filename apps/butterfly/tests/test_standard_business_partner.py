import json

import pytest
from conftest import make_client

from butterfly.application.alpha import external as ext
from butterfly.infrastructure.api.standard.business_partner import ROOT
from butterfly.infrastructure.api.standard.edmx import PARTNER_METADATA, SPECS
from butterfly.infrastructure.memory.companies import COMPANIES

SAMPLES = SPECS / "api_business_partner-v2"


def real_row(name: str) -> dict:
    return json.loads((SAMPLES / name).read_text())["d"]["results"][0]


REAL = {
    "A_Customer": real_row("customers-top3.json"),
    "A_CustomerCompany": real_row("customer-companies-top3.json"),
    "A_CustomerSalesArea": real_row("customer-sales-areas-top3.json"),
    "A_Supplier": real_row("suppliers-top3.json"),
    "A_SupplierCompany": real_row("supplier-companies-top3.json"),
    "A_SupplierPurchasingOrg": real_row("supplier-purchasing-orgs-top3.json"),
}
CUSTOMERS = [(c.customer_id, company.code) for company in COMPANIES for c in company.customers]
SUPPLIERS = [(sid, name, company.code) for company in COMPANIES for sid, name in company.suppliers]
FIRST_CUSTOMER, FIRST_COMPANY = CUSTOMERS[0]


@pytest.fixture(scope="module")
def client():
    return make_client()


def get(client, path):
    return client.get(f"{ROOT}/{path}")


def kind(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


class TestTheRealMetadata:
    def test_is_the_saved_real_document(self, client):
        assert get(client, "$metadata").content == PARTNER_METADATA.read_bytes()


class TestRows:
    @pytest.mark.parametrize("entity", list(REAL))
    def test_has_exactly_the_properties_and_types_of_the_real_row(self, client, entity):
        row = get(client, f"{entity}?$top=1").json()["d"]["results"][0]
        real = REAL[entity]
        assert list(row) == list(real)
        assert [n for n in real if real[n] is not None and row[n] is not None and kind(row[n]) != kind(real[n]) and n != "__metadata"] == []
        assert list(row["__metadata"]) == list(real["__metadata"]) and row["__metadata"]["type"].startswith("API_BUSINESS_PARTNER.")

    def test_every_customer_is_listed_with_its_name(self, client):
        rows = get(client, "A_Customer?$top=100&$select=Customer,CustomerName").json()["d"]["results"]
        assert {r["Customer"] for r in rows} == {ext(c) for c, _ in CUSTOMERS}
        assert all(r["CustomerName"] for r in rows)

    def test_a_customer_has_a_company_row_and_a_sales_area_row(self, client):
        companies = get(client, f"A_CustomerCompany?$filter=Customer eq '{FIRST_CUSTOMER}'").json()["d"]["results"]
        areas = get(client, f"A_CustomerSalesArea?$filter=Customer eq '{FIRST_CUSTOMER}'").json()["d"]["results"]
        assert [c["CompanyCode"] for c in companies] == [FIRST_COMPANY]
        assert [(a["SalesOrganization"], a["DistributionChannel"], a["Division"]) for a in areas] == [(areas[0]["SalesOrganization"], "10", "00")]
        assert areas[0]["SalesOrganization"]

    def test_every_supplier_is_listed_with_its_company_and_purchasing_organization(self, client):
        rows = get(client, "A_Supplier?$top=100&$select=Supplier,SupplierName").json()["d"]["results"]
        assert {(r["Supplier"], r["SupplierName"]) for r in rows} == {(ext(s), n) for s, n, _ in SUPPLIERS}
        first = SUPPLIERS[0]
        companies = get(client, f"A_SupplierCompany?$filter=Supplier eq '{first[0]}'").json()["d"]["results"]
        orgs = get(client, f"A_SupplierPurchasingOrg?$filter=Supplier eq '{first[0]}'").json()["d"]["results"]
        assert [c["CompanyCode"] for c in companies] == [first[2]] and orgs[0]["PurchasingOrganization"] and orgs[0]["PurchasingGroup"] == "001"

    def test_a_key_gets_one_row_and_composite_keys_work(self, client):
        assert get(client, f"A_Customer('{FIRST_CUSTOMER}')").json()["d"]["Customer"] == ext(FIRST_CUSTOMER)
        assert get(client, f"A_CustomerCompany(Customer='{FIRST_CUSTOMER}',CompanyCode='{FIRST_COMPANY}')").json()["d"]["CompanyCode"] == FIRST_COMPANY
        assert get(client, f"A_CustomerCompany(Customer='{FIRST_CUSTOMER}',CompanyCode='ZZZZ')").status_code == 404


class TestByCompany:
    def test_customers_of_one_company_through_the_company_rows(self, client):
        rows = get(client, "A_CustomerCompany?$filter=CompanyCode eq 'INA2'&$top=100&$select=Customer").json()["d"]["results"]
        assert {r["Customer"] for r in rows} == {ext(c) for c, code in CUSTOMERS if code == "INA2"}

    def test_suppliers_of_one_company_through_the_company_rows(self, client):
        rows = get(client, "A_SupplierCompany?$filter=CompanyCode eq 'INA3'&$top=100&$select=Supplier").json()["d"]["results"]
        assert {r["Supplier"] for r in rows} == {ext(s) for s, _, code in SUPPLIERS if code == "INA3"}


class TestSearching:
    def test_by_the_start_of_the_number(self, client):
        rows = get(client, f"A_Customer?$filter=startswith(Customer,'{FIRST_CUSTOMER[:6]}')&$select=Customer").json()["d"]["results"]
        assert rows and all(r["Customer"].startswith(ext(FIRST_CUSTOMER)[:4]) or r["Customer"].startswith(FIRST_CUSTOMER[:6]) for r in rows)

    def test_by_a_word_of_the_name_the_v2_way(self, client):
        name = get(client, f"A_Customer('{FIRST_CUSTOMER}')").json()["d"]["CustomerName"]
        word = name.split()[0]
        body = get(client, f"A_Customer?$filter=substringof('{word}',CustomerName)&$inlinecount=allpages&$select=Customer,CustomerName").json()["d"]
        assert body["__count"] == str(len(body["results"])) and ext(FIRST_CUSTOMER) in {r["Customer"] for r in body["results"]}

    def test_pages_and_counts_as_a_string(self, client):
        body = get(client, "A_Customer?$top=2&$skip=1&$inlinecount=allpages&$select=Customer&$orderby=Customer").json()["d"]
        assert len(body["results"]) == 2 and body["__count"] == str(len(CUSTOMERS))

    def test_count_segment_is_plain_text(self, client):
        response = get(client, "A_Supplier/$count")
        assert response.text == str(len(SUPPLIERS)) and response.headers["content-type"].startswith("text/plain")


class TestNavigating:
    def test_expands_the_company_rows_of_a_customer(self, client):
        row = get(client, f"A_Customer?$filter=Customer eq '{FIRST_CUSTOMER}'&$expand=to_CustomerCompany").json()["d"]["results"][0]
        assert [c["CompanyCode"] for c in row["to_CustomerCompany"]["results"]] == [FIRST_COMPANY]
        assert "__deferred" in row["to_CustomerSalesArea"]

    def test_an_expanded_list_shows_only_when_the_navigation_is_selected(self, client):
        plain = get(client, "A_Customer?$top=1&$select=Customer&$expand=to_CustomerCompany").json()["d"]["results"][0]
        assert list(plain) == ["__metadata", "Customer"]
        chosen = get(client, "A_Customer?$top=1&$select=Customer,to_CustomerCompany&$expand=to_CustomerCompany").json()["d"]["results"][0]
        assert chosen["to_CustomerCompany"]["results"]

    def test_a_row_links_to_its_navigation_paths(self, client):
        row = get(client, "A_Customer?$top=1").json()["d"]["results"][0]
        assert row["to_CustomerCompany"]["__deferred"]["uri"].endswith(f"/A_Customer('{row['Customer']}')/to_CustomerCompany")

    def test_a_navigation_path_lists_the_children(self, client):
        rows = get(client, f"A_Customer('{FIRST_CUSTOMER}')/to_CustomerSalesArea").json()["d"]["results"]
        assert len(rows) == 1 and rows[0]["Customer"] == ext(FIRST_CUSTOMER)

    def test_the_count_comes_before_the_results(self, client):
        assert list(get(client, "A_Customer?$top=1&$inlinecount=allpages&$select=Customer").json()["d"]) == ["__count", "results"]

    def test_the_other_entity_sets_answer_empty(self, client):
        assert get(client, "A_BusinessPartnerBank").json() == {"d": {"results": []}}


def real_error(name: str) -> dict:
    return json.loads((SAMPLES / f"{name}.json").read_text())["error"]


class TestPartnersOfTheCustomers:
    def test_every_customer_is_a_partner_with_the_customer_roles(self, client):
        partner = get(client, f"A_BusinessPartner('{FIRST_CUSTOMER}')").json()["d"]
        roles = get(client, f"A_BusinessPartner('{FIRST_CUSTOMER}')/to_BusinessPartnerRole").json()["d"]["results"]
        assert partner["BusinessPartner"] == partner["Customer"] == ext(FIRST_CUSTOMER) and partner["BusinessPartnerCategory"] == "2"
        assert {r["BusinessPartnerRole"] for r in roles} == {"FLCU00", "FLCU01"}

    def test_the_address_carries_the_country(self, client):
        rows = get(client, f"A_BusinessPartner('{FIRST_CUSTOMER}')/to_BusinessPartnerAddress").json()["d"]["results"]
        assert len(rows) == 1 and rows[0]["Country"] and rows[0]["AddressID"] == "1"

    def test_a_partner_row_has_the_property_names_of_the_real_sample(self, client):
        row = get(client, f"A_BusinessPartner('{FIRST_CUSTOMER}')").json()["d"]
        assert set(real_row("partners-top2.json")) - {"__metadata"} <= set(row)


class TestRefusalsLikeTheSandbox:
    @pytest.mark.parametrize(
        "path, status, sample",
        [
            ("A_Customer('NOPE')", 404, "error-not-found"),
            ("A_Customer?$filter=Nope eq 1", 400, "error-bad-filter"),
            ("A_Customer?$select=Nope", 404, "error-unknown-select"),
            ("A_Customer?$expand=to_Nope", 404, "error-unknown-expand"),
            ("A_Customer?$foo=1", 400, "error-unknown-option"),
            ("A_Customer?$top=abc", 400, "error-bad-top"),
            ("A_Customer?$orderby=Nope", 400, "error-bad-orderby"),
        ],
    )
    def test_gives_the_status_code_and_message_of_the_sample(self, client, path, status, sample):
        response = get(client, path)
        error, real = response.json()["error"], real_error(sample)
        assert response.status_code == status
        assert (error["code"], error["message"]) == (real["code"], real["message"])
        assert list(error["innererror"]) == list(real["innererror"])


class TestNumbersWithoutLeadingZeros:
    def test_a_customer_number_is_shown_without_leading_zeros(self, client):
        numbers = [r["Customer"] for r in get(client, "A_Customer?$top=100&$select=Customer").json()["d"]["results"]]
        assert numbers and all(not n.startswith("0") for n in numbers)

    def test_a_supplier_number_is_shown_without_leading_zeros(self, client):
        numbers = [r["Supplier"] for r in get(client, "A_Supplier?$top=100&$select=Supplier").json()["d"]["results"]]
        assert numbers and all(not n.startswith("0") for n in numbers)

    def test_a_key_finds_the_same_customer_with_or_without_the_zeros(self, client):
        padded = get(client, f"A_Customer('{FIRST_CUSTOMER}')").json()["d"]
        plain = get(client, f"A_Customer('{ext(FIRST_CUSTOMER)}')").json()["d"]
        assert padded["Customer"] == plain["Customer"] == ext(FIRST_CUSTOMER)

    def test_a_filter_finds_the_same_customer_with_or_without_the_zeros(self, client):
        for text in (FIRST_CUSTOMER, ext(FIRST_CUSTOMER)):
            rows = get(client, f"A_Customer?$filter=Customer eq '{text}'&$select=Customer").json()["d"]["results"]
            assert [r["Customer"] for r in rows] == [ext(FIRST_CUSTOMER)]

    def test_the_company_rows_follow_the_same_number(self, client):
        rows = get(client, f"A_CustomerCompany?$filter=Customer eq '{ext(FIRST_CUSTOMER)}'").json()["d"]["results"]
        assert [r["CompanyCode"] for r in rows] == [FIRST_COMPANY]

    def test_a_number_that_is_not_all_digits_is_left_alone(self, client):
        assert get(client, "A_Customer('NOPE-1')").status_code == 404

    def test_a_search_by_the_start_of_the_shown_number_finds_it(self, client):
        rows = get(client, f"A_Customer?$filter=startswith(Customer,'{ext(FIRST_CUSTOMER)[:4]}')&$select=Customer").json()["d"]["results"]
        assert ext(FIRST_CUSTOMER) in {r["Customer"] for r in rows}
