import copy

import pytest
from conftest import make_client

from butterfly.infrastructure.api.standard.business_partner import ROOT

BODY = {
    "BusinessPartnerCategory": "2",
    "BusinessPartnerGrouping": "BP02",
    "OrganizationBPName1": "Lakefront Wellness Inc",
    "to_BusinessPartnerRole": {"results": [{"BusinessPartnerRole": "FLCU00"}, {"BusinessPartnerRole": "FLCU01"}]},
    "to_BusinessPartnerAddress": {"results": [{"Country": "US", "CityName": "Austin", "PostalCode": "73301", "StreetName": "Main Street", "Language": "EN"}]},
    "to_Customer": {
        "CustomerAccountGroup": "CUST",
        "to_CustomerCompany": {"results": [{"CompanyCode": "INA1", "ReconciliationAccount": "12100000", "PaymentTerms": "0001"}]},
        "to_CustomerSalesArea": {"results": [{"SalesOrganization": "1010", "DistributionChannel": "10", "Division": "00", "Currency": "USD"}]},
    },
}


@pytest.fixture
def client():
    return make_client()


def post(client, **changes):
    body = copy.deepcopy(BODY) | changes
    return client.post(f"{ROOT}/A_BusinessPartner", json=body)


def get(client, path):
    return client.get(f"{ROOT}/{path}")


class TestCreatingACustomer:
    def test_answers_201_with_the_new_number_without_leading_zeros(self, client):
        response = post(client)
        row = response.json()["d"]
        assert response.status_code == 201
        assert row["BusinessPartner"] == row["Customer"] == "200000"
        assert row["OrganizationBPName1"] == "Lakefront Wellness Inc" and row["SearchTerm1"] == "LAKEFRONT"

    def test_the_customer_is_then_read_from_every_set(self, client):
        post(client)
        assert get(client, "A_BusinessPartner('200000')").status_code == 200
        assert get(client, "A_Customer('200000')").json()["d"]["CustomerName"] == "Lakefront Wellness Inc"
        assert get(client, "A_CustomerCompany(Customer='200000',CompanyCode='INA1')").status_code == 200
        address = get(client, "A_BusinessPartner('200000')/to_BusinessPartnerAddress").json()["d"]["results"][0]
        assert address["Country"] == "US" and address["CityName"] == "Austin"
        roles = get(client, "A_BusinessPartner('200000')/to_BusinessPartnerRole").json()["d"]["results"]
        assert {r["BusinessPartnerRole"] for r in roles} == {"FLCU00", "FLCU01"}

    def test_the_customer_shows_in_the_customer_list(self, client):
        post(client)
        names = {r["CustomerName"] for r in get(client, "A_Customer?$filter=startswith(CustomerName,'Lakefront')").json()["d"]["results"]}
        assert names == {"Lakefront Wellness Inc"}


class TestNumbers:
    def test_two_creates_give_two_numbers(self, client):
        assert [post(client).json()["d"]["BusinessPartner"] for _ in range(2)] == ["200000", "200001"]

    def test_a_sent_number_is_kept(self, client):
        assert post(client, BusinessPartner="350000").json()["d"]["BusinessPartner"] == "350000"

    def test_a_sent_number_that_exists_is_refused(self, client):
        post(client, BusinessPartner="350000")
        response = post(client, BusinessPartner="350000")
        assert response.status_code == 400
        assert "already exists" in response.json()["error"]["message"]["value"]


class TestRefusals:
    @pytest.mark.parametrize(
        "changes, target",
        [
            ({"OrganizationBPName1": ""}, "OrganizationBPName1"),
            ({"BusinessPartnerCategory": "1"}, "BusinessPartnerCategory"),
            ({"to_BusinessPartnerRole": {"results": []}}, "to_BusinessPartnerRole"),
            ({"to_BusinessPartnerAddress": {"results": [{"CityName": "Austin"}]}}, "to_BusinessPartnerAddress/Country"),
            ({"to_BusinessPartnerAddress": {"results": [{"Country": "Narnia"}]}}, "to_BusinessPartnerAddress/Country"),
            ({"BusinessPartner": "ABC"}, "BusinessPartner"),
        ],
    )
    def test_each_refusal_names_its_field_and_stores_nothing(self, client, changes, target):
        response = post(client, **changes)
        assert response.status_code == 400
        assert target in {d["target"] for d in response.json()["error"]["innererror"]["errordetails"]}
        assert get(client, "A_BusinessPartner/$count").text == str(len(get(client, "A_Customer").json()["d"]["results"]))
        assert post(client).json()["d"]["BusinessPartner"] == "200000"

    def test_missing_customer_data_is_refused(self, client):
        body = {key: value for key, value in BODY.items() if key != "to_Customer"}
        response = client.post(f"{ROOT}/A_BusinessPartner", json=body)
        assert response.status_code == 400

    def test_unknown_company_currency_and_wrong_sales_organization(self, client):
        customer = copy.deepcopy(BODY["to_Customer"])
        customer["to_CustomerCompany"]["results"][0]["CompanyCode"] = "ZZZZ"
        customer["to_CustomerSalesArea"]["results"][0]["Currency"] = "XXX"
        targets = {d["target"] for d in post(client, to_Customer=customer).json()["error"]["innererror"]["errordetails"]}
        assert targets == {
            "to_Customer/to_CustomerCompany/CompanyCode",
            "to_Customer/to_CustomerSalesArea/Currency",
            "to_Customer/to_CustomerSalesArea/SalesOrganization",
        }

    def test_a_body_that_is_not_json_is_refused(self, client):
        assert client.post(f"{ROOT}/A_BusinessPartner", content="not json").status_code == 400
