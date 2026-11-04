import pytest

pytest.importorskip("butterfly")
from fastapi.testclient import TestClient
from test_butterfly_requisition_gateway import InProcessButterfly, Unreachable, gateway
from test_routes_access import SECRET, token_with
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from butterfly.infrastructure.memory.in_memory_master_data_repo import InMemoryMasterDataRepo
from workspace_api.entrypoint.app import create_app
from workspace_api.infrastructure.mock_purchase_requisition_gateway import MockPurchaseRequisitionGateway
from workspace_api.infrastructure.mock_sales_order_gateway import MockSalesOrderGateway
from workspace_api.infrastructure.settings import Settings

URL = "/v1/workspace/purchase-requisitions"
MATERIALS = {m.company_code: m for m in InMemoryMasterDataRepo().materials.values()}
MINE = MATERIALS["INA1"]
THEIRS = MATERIALS["INA2"]


def body(material=MINE, plant="1000", quantity="5", **item):
    return {
        "description": "Spare parts",
        "items": [{"material": material.material_id, "plant": plant, "quantity": quantity, "unit": material.unit, "delivery_date": "2026-12-01"} | item],
    }


def client_for(roles, companies=None, requisitions=None) -> TestClient:
    app = create_app(MockSalesOrderGateway(), Settings(jwt_secret=SECRET), requisitions=requisitions or gateway())
    client = TestClient(app)
    if roles is not None:
        client.cookies.set(ACCESS_TOKEN_COOKIE, token_with(roles, companies))
    return client


def purchase(requisitions=None) -> TestClient:
    return client_for(["purchase"], ["sabinsa"], requisitions)


class TestWhoMayDoWhat:
    def test_no_cookie_is_401(self):
        assert client_for(None).post(URL, json=body()).status_code == 401

    @pytest.mark.parametrize("roles", [["sales"], ["management"], ["stores"], ["admin"]])
    def test_only_purchase_creates(self, roles):
        assert client_for(roles, ["sabinsa"]).post(URL, json=body()).status_code == 403

    @pytest.mark.parametrize("roles, status", [(["purchase"], 200), (["management"], 200), (["sales"], 403), (["stores"], 403)])
    def test_purchase_and_management_read(self, roles, status):
        assert client_for(roles, ["sabinsa"]).get(URL).status_code == status

    def test_only_management_releases(self):
        shared = gateway()
        purchase(shared).post(URL, json=body(quantity="5000000"))
        release = {"release_code": "01"}
        assert client_for(["purchase"], ["sabinsa"], shared).post(f"{URL}/10000000/release", json=release).status_code == 403
        assert client_for(["management"], ["sabinsa"], shared).post(f"{URL}/10000000/release", json=release).status_code == 200


class TestCreating:
    def test_returns_201_with_the_numbers_amounts_and_status_words(self):
        response = purchase().post(URL, json=body(text="for the line"))
        created = response.json()
        assert response.status_code == 201 and created["purchase_requisition"] == "10000000"
        item = created["items"][0]
        assert item["item"] == "10" and item["company_code"] == "INA1" and item["text"] == "for the line"
        assert item["release_status"] == "released" and item["release_status_code"] == "03" and item["ordered"] is False
        assert float(created["total_net_amount"]) == float(item["net_amount"]) > 0

    def test_an_item_that_needs_release_says_so(self):
        assert purchase().post(URL, json=body(quantity="5000000")).json()["items"][0]["release_status"] == "not_released"

    def test_a_plant_of_another_company_is_403_and_nothing_is_created(self):
        shared = gateway()
        response = purchase(shared).post(URL, json=body(THEIRS, plant="2000"))
        assert (response.status_code, response.json()["code"]) == (403, "COMPANY_NOT_ALLOWED")
        assert shared.list_recent(10, 0, ["INA1", "INA2"]).total == 0

    def test_an_unknown_plant_is_403(self):
        assert purchase().post(URL, json=body(plant="9999")).status_code == 403

    def test_butterflys_refusal_is_422_with_the_workspace_field(self):
        sent = body()
        sent["items"][0]["material"] = "NOPE"
        response = purchase().post(URL, json=sent)
        assert response.status_code == 422 and response.json()["code"] == "VALIDATION_FAILED"
        assert [(d["code"], d["target"]) for d in response.json()["details"]] == [("MATERIAL_UNKNOWN", "items/0/material")]

    def test_a_requisition_without_items_is_422(self):
        assert purchase().post(URL, json={"description": "x", "items": []}).status_code == 422

    def test_the_mock_gateway_can_also_refuse(self):
        from workspace_api.domain.errors import ValidationDetail

        mock = MockPurchaseRequisitionGateway()
        mock.reject_with([ValidationDetail("X", "bad", "items/0/quantity")])
        assert purchase(mock).post(URL, json=body()).json()["details"][0]["target"] == "items/0/quantity"


class TestReading:
    def test_lists_newest_first_with_the_total_and_pages(self):
        shared = gateway()
        for _ in range(3):
            purchase(shared).post(URL, json=body())
        page = purchase(shared).get(f"{URL}?top=2").json()
        assert [r["purchase_requisition"] for r in page["requisitions"]] == ["10000002", "10000001"] and page["total"] == 3
        assert [r["purchase_requisition"] for r in purchase(shared).get(f"{URL}?top=2&skip=2").json()["requisitions"]] == ["10000000"]

    def test_lists_only_the_users_companies(self):
        shared = gateway()
        client_for(["purchase"], ["sabinsa", "organica"], shared).post(URL, json=body(THEIRS, plant="2000"))
        purchase(shared).post(URL, json=body())
        assert purchase(shared).get(URL).json()["total"] == 1

    def test_a_requisition_of_another_company_is_404(self):
        shared = gateway()
        client_for(["purchase"], ["sabinsa", "organica"], shared).post(URL, json=body(THEIRS, plant="2000"))
        assert purchase(shared).get(f"{URL}/10000000").status_code == 404

    def test_opens_one_requisition_and_an_unknown_number_is_404(self):
        shared = gateway()
        purchase(shared).post(URL, json=body())
        assert purchase(shared).get(f"{URL}/10000000").json()["items"][0]["material"] == MINE.material_id
        assert purchase(shared).get(f"{URL}/10000099").status_code == 404

    @pytest.mark.parametrize("query", ["top=0", "top=101", "skip=-1"])
    def test_a_bad_page_is_422(self, query):
        assert purchase().get(f"{URL}?{query}").status_code == 422


class TestReleasing:
    def manager(self, shared) -> TestClient:
        return client_for(["management"], ["sabinsa"], shared)

    def test_releases_step_by_step(self):
        shared = gateway()
        purchase(shared).post(URL, json=body(quantity="5000000"))
        first = self.manager(shared).post(f"{URL}/10000000/release", json={"release_code": "01"}).json()
        assert first["items"][0]["release_status"] == "in_release"
        second = self.manager(shared).post(f"{URL}/10000000/release", json={"release_code": "02", "item": "10"}).json()
        assert second["items"][0]["release_status"] == "released"

    def test_butterflys_refusal_is_422(self):
        shared = gateway()
        purchase(shared).post(URL, json=body(quantity="5000000"))
        response = self.manager(shared).post(f"{URL}/10000000/release", json={"release_code": "02"})
        assert response.status_code == 422 and "not the next code" in response.json()["details"][0]["message"]

    def test_another_companys_requisition_cannot_be_released(self):
        shared = gateway()
        client_for(["purchase"], ["organica"], shared).post(URL, json=body(THEIRS, plant="2000", quantity="5000000"))
        assert self.manager(shared).post(f"{URL}/10000000/release", json={"release_code": "01"}).status_code == 404

    def test_a_release_without_a_code_is_422(self):
        assert self.manager(gateway()).post(f"{URL}/10000000/release", json={}).status_code == 422


class TestWhenButterflyIsDown:
    @pytest.mark.parametrize("method, path, payload", [("post", URL, body()), ("get", URL, None), ("get", f"{URL}/10000000", None)])
    def test_answers_503_and_says_so(self, method, path, payload):
        client = purchase(gateway(Unreachable()))
        response = getattr(client, method)(path, **({"json": payload} if payload else {}))
        assert (response.status_code, response.json()["code"]) == (503, "SAP_UNAVAILABLE")

    def test_release_answers_503(self):
        client = client_for(["management"], ["sabinsa"], gateway(Unreachable()))
        assert client.post(f"{URL}/10000000/release", json={"release_code": "01"}).status_code == 503
