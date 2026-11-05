import pytest

pytest.importorskip("butterfly")
from fastapi.testclient import TestClient
from test_butterfly_master_data_gateway import gateway
from test_butterfly_requisition_gateway import Unreachable
from test_routes_access import SECRET, token_with
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from butterfly.infrastructure.memory.companies import COMPANIES
from workspace_api.domain.entities.master_data import BusinessPartner, Material, Plant
from workspace_api.entrypoint.app import create_app
from workspace_api.infrastructure.mock_master_data_gateway import MockMasterDataGateway
from workspace_api.infrastructure.mock_sales_order_gateway import MockSalesOrderGateway
from workspace_api.infrastructure.settings import Settings

BASE = "/v1/workspace/master-data"
INA1 = COMPANIES[0]


def client_for(roles, companies=None, master=None) -> TestClient:
    app = create_app(MockSalesOrderGateway(), Settings(jwt_secret=SECRET), master_data=master or gateway())
    client = TestClient(app)
    if roles is not None:
        client.cookies.set(ACCESS_TOKEN_COOKIE, token_with(roles, companies))
    return client


def purchase(master=None) -> TestClient:
    return client_for(["purchase"], ["sabinsa"], master)


def sales(master=None) -> TestClient:
    return client_for(["sales"], ["sabinsa"], master)


class TestWhoMayRead:
    def test_no_cookie_is_401(self):
        assert client_for(None).get(f"{BASE}/plants").status_code == 401

    @pytest.mark.parametrize("roles, status", [(["purchase"], 200), (["sales"], 200), (["management"], 200), (["stores"], 403), (["admin"], 403)])
    def test_plants(self, roles, status):
        assert client_for(roles, ["sabinsa"]).get(f"{BASE}/plants").status_code == status

    @pytest.mark.parametrize("roles, status", [(["purchase"], 200), (["sales"], 200), (["management"], 403), (["stores"], 403)])
    def test_materials(self, roles, status):
        assert client_for(roles, ["sabinsa"]).get(f"{BASE}/materials").status_code == status

    @pytest.mark.parametrize("roles, status", [(["sales"], 200), (["purchase"], 403), (["management"], 403)])
    def test_customers_are_for_sales(self, roles, status):
        assert client_for(roles, ["sabinsa"]).get(f"{BASE}/customers").status_code == status

    @pytest.mark.parametrize("roles, status", [(["purchase"], 200), (["sales"], 403), (["management"], 403)])
    def test_suppliers_are_for_purchase(self, roles, status):
        assert client_for(roles, ["sabinsa"]).get(f"{BASE}/suppliers").status_code == status


class TestPlants:
    def test_only_the_plants_of_the_users_companies_with_their_company(self):
        plants = purchase().get(f"{BASE}/plants").json()["plants"]
        assert [(p["plant"], p["company_code"]) for p in plants] == [("1000", "INA1")] and plants[0]["name"]

    def test_a_user_with_two_companies_sees_both(self):
        plants = client_for(["purchase"], ["sabinsa", "organica"]).get(f"{BASE}/plants").json()["plants"]
        assert [(p["plant"], p["company_code"]) for p in plants] == [("1000", "INA1"), ("3000", "INA3")]

    def test_a_user_without_companies_sees_none(self):
        assert client_for(["purchase"], []).get(f"{BASE}/plants").json() == {"plants": []}


class TestMaterials:
    def test_lists_the_materials_of_the_users_plants_with_unit_and_description(self):
        body = purchase().get(f"{BASE}/materials?top=50").json()
        first = next(m for m in body["materials"] if m["material"] == "RM-1001")
        assert first == {"material": "RM-1001", "description": "Curcumin extract 95%", "unit": "KG", "iso_unit": "KGM", "material_group": "EXTRACT", "material_type": "FERT", "plants": ["1000"]}
        assert body["total"] == len(INA1.materials) + len(INA1.raw_materials)

    def test_one_plant_of_the_user(self):
        assert purchase().get(f"{BASE}/materials?plant=1000").json()["total"] > 0

    def test_a_plant_of_another_company_is_403(self):
        response = purchase().get(f"{BASE}/materials?plant=2000")
        assert (response.status_code, response.json()["code"]) == (403, "COMPANY_NOT_ALLOWED")

    def test_searches_by_number_and_by_description(self):
        assert purchase().get(f"{BASE}/materials?q=RAW-200").json()["total"] > 0
        assert purchase().get(f"{BASE}/materials?q=Turmeric").json()["total"] > 0

    def test_a_search_with_quotes_is_safe(self):
        assert purchase().get(f"{BASE}/materials", params={"q": "x' or 1 eq 1 or 'y"}).json()["total"] == 0

    @pytest.mark.parametrize("query", ["top=0", "top=51", "skip=-1", "q=" + "x" * 41])
    def test_bad_limits_are_422(self, query):
        response = purchase().get(f"{BASE}/materials?{query}")
        assert (response.status_code, response.json()["code"]) == (422, "INVALID_QUERY")

    def test_sales_can_use_it_for_the_order_form(self):
        assert sales().get(f"{BASE}/materials").json()["total"] > 0


class TestCustomersAndSuppliers:
    def test_customers_of_the_users_company_only(self):
        body = sales().get(f"{BASE}/customers?top=50").json()
        assert {c["number"] for c in body["customers"]} == {c.customer_id for c in INA1.customers} and body["total"] == len(INA1.customers)
        assert all(c["company_codes"] == ["INA1"] and c["name"] for c in body["customers"])

    def test_customers_are_searched_by_number_and_name(self):
        target = INA1.customers[0]
        assert target.customer_id in {c["number"] for c in sales().get(f"{BASE}/customers", params={"q": target.name.split()[0]}).json()["customers"]}
        assert [c["number"] for c in sales().get(f"{BASE}/customers", params={"q": target.customer_id}).json()["customers"]] == [target.customer_id]

    def test_suppliers_of_the_users_company_only(self):
        body = purchase().get(f"{BASE}/suppliers").json()
        assert {(s["number"], s["name"]) for s in body["suppliers"]} == set(INA1.suppliers)

    def test_pages(self):
        body = sales().get(f"{BASE}/customers?top=2&skip=1").json()
        assert len(body["customers"]) == 2 and body["total"] == len(INA1.customers)


class TestWhenButterflyIsDown:
    @pytest.mark.parametrize("path, make", [("plants", purchase), ("materials", purchase), ("customers", sales), ("suppliers", purchase)])
    def test_answers_503(self, path, make):
        response = make(gateway(Unreachable())).get(f"{BASE}/{path}")
        assert (response.status_code, response.json()["code"]) == (503, "SAP_UNAVAILABLE")


class TestWithTheMock:
    def test_the_routes_work_with_any_gateway(self):
        mock = MockMasterDataGateway(
            [Plant("1000", "Plant A")], [Material("M1", "Bolt", "PC", "PCE", "G", "FERT", ["1000"])], [BusinessPartner("C1", "Acme", ["INA1"])], [BusinessPartner("S1", "Supply", ["INA1"])]
        )
        assert purchase(mock).get(f"{BASE}/plants").json()["plants"][0]["name"] == "Plant A"
        assert purchase(mock).get(f"{BASE}/materials?q=Bolt").json()["materials"][0]["material"] == "M1"
        assert sales(mock).get(f"{BASE}/customers").json()["customers"][0]["name"] == "Acme"
        assert purchase(mock).get(f"{BASE}/suppliers").json()["suppliers"][0]["number"] == "S1"
