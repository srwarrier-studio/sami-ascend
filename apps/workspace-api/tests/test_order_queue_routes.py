from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from test_routes_access import SECRET, VALID_BODY
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from workspace_api.domain.entities.order_request import QUEUED, UNKNOWN
from workspace_api.domain.errors import SalesOrderRejected, SapNotReached, SapOutcomeUnknown, SapUnavailable, ValidationDetail
from workspace_api.entrypoint.app import create_app
from workspace_api.infrastructure.mock_sales_order_gateway import MockSalesOrderGateway
from workspace_api.infrastructure.settings import Settings
from workspace_api.infrastructure.sqlite_order_request_store import SqliteOrderRequestStore

URL = "/v1/workspace/sales-orders"
REQUESTS = "/v1/workspace/sales-order-requests"


def token(user="user-1", roles=("sales",)):
    payload = {"sub": user, "sap_username": f"SAP_{user}", "roles": list(roles), "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    return jwt.encode(payload, SECRET, algorithm="HS256")


def make(gateway=None, store=None, user="user-1", roles=("sales",)):
    gateway = gateway or MockSalesOrderGateway()
    store = store or SqliteOrderRequestStore(":memory:")
    client = TestClient(create_app(gateway, Settings(jwt_secret=SECRET), store))
    if roles is not None:
        client.cookies.set(ACCESS_TOKEN_COOKIE, token(user, roles))
    return client, gateway, store


def failing(gateway, error):
    def create(order):
        raise error

    gateway.create = create


class TestWhenSapAnswers:
    def test_a_posted_order_is_201_and_nothing_is_saved(self):
        client, _, store = make()
        response = client.post(URL, json=VALID_BODY)
        assert response.status_code == 201 and response.json()["sales_order"] == "0000000001"
        assert store.list_open("user-1", 50) == []

    def test_a_rejection_is_422_with_details_and_nothing_is_saved(self):
        gateway = MockSalesOrderGateway()
        gateway.reject_with([ValidationDetail("CUSTOMER_UNKNOWN", "x", "SoldToParty")])
        client, _, store = make(gateway)
        response = client.post(URL, json=VALID_BODY)
        assert response.status_code == 422 and response.json()["details"][0]["code"] == "CUSTOMER_UNKNOWN"
        assert store.list_open("user-1", 50) == []


class TestWhenSapCannotTakeIt:
    def test_not_processed_is_202_queued_and_saved(self):
        client, gateway, store = make()
        failing(gateway, SapNotReached("refused"))
        response = client.post(URL, json=VALID_BODY)
        body = response.json()
        assert response.status_code == 202 and body["status"] == QUEUED and body["attempts"] == 0
        assert "saved and will be sent automatically" in body["message"]
        [saved] = store.list_open("user-1", 50)
        assert (saved.id, saved.status) == (body["id"], QUEUED)

    def test_the_saved_order_keeps_the_user_the_sap_user_the_request_id_and_the_body(self):
        client, gateway, store = make()
        failing(gateway, SapNotReached("refused"))
        response = client.post(URL, json=VALID_BODY)
        [saved] = store.list_open("user-1", 50)
        assert (saved.user, saved.sap_username, saved.request_id) == ("user-1", "SAP_user-1", response.headers["x-request-id"])
        assert saved.body["sold_to_party"] == "0000100001" and saved.body["items"][0]["quantity"] == "50.000"

    def test_an_unclear_result_is_202_unknown_and_tells_the_user_to_check(self):
        client, gateway, store = make()
        failing(gateway, SapOutcomeUnknown("timeout"))
        body = client.post(URL, json=VALID_BODY).json()
        assert body["status"] == UNKNOWN and "Check the order list" in body["message"]
        assert store.list_open("user-1", 50)[0].status == UNKNOWN

    def test_any_other_unavailable_is_503_and_nothing_is_saved(self):
        client, gateway, store = make()
        failing(gateway, SapUnavailable("odd"))
        response = client.post(URL, json=VALID_BODY)
        assert (response.status_code, response.json()) == (503, {"code": "SAP_UNAVAILABLE"})
        assert store.list_open("user-1", 50) == []

    def test_without_a_store_it_stays_a_503_as_before(self):
        gateway = MockSalesOrderGateway()
        failing(gateway, SapNotReached("refused"))
        client = TestClient(create_app(gateway, Settings(jwt_secret=SECRET)))
        client.cookies.set(ACCESS_TOKEN_COOKIE, token())
        assert client.post(URL, json=VALID_BODY).status_code == 503
        assert client.get(REQUESTS).status_code == 404

    def test_if_the_order_cannot_even_be_saved_the_user_gets_a_503(self):
        client, gateway, store = make()
        failing(gateway, SapNotReached("refused"))
        store.db.close()
        response = client.post(URL, json=VALID_BODY)
        assert (response.status_code, response.json()) == (503, {"code": "STORE_UNAVAILABLE"})


class TestTheSavedOrderIsShown:
    def queued(self):
        client, gateway, _ = make()
        failing(gateway, SapNotReached("refused"))
        return client, client.post(URL, json=VALID_BODY)

    def test_the_202_the_status_and_the_list_all_carry_the_order_as_sent(self):
        client, response = self.queued()
        sent = {"sales_order_type": "OR", "sold_to_party": "0000100001", "transaction_currency": "INR", "requested_delivery_date": "2026-11-05",
                "items": [{"material": "RM-1001", "quantity": "50.000", "quantity_unit": "KG"}]}
        request_id = response.json()["id"]
        assert response.json()["order"] == sent
        assert client.get(f"{REQUESTS}/{request_id}").json()["order"] == sent
        assert client.get(REQUESTS).json()["requests"][0]["order"] == sent

    def test_it_is_only_shown_to_its_owner(self):
        client, response = self.queued()
        other = TestClient(create_app(MockSalesOrderGateway(), Settings(jwt_secret=SECRET), SqliteOrderRequestStore(":memory:")))
        other.cookies.set(ACCESS_TOKEN_COOKIE, token("user-2"))
        assert other.get(f"{REQUESTS}/{response.json()['id']}").status_code == 404


class TestSeeingWhatHappened:
    def queued(self, client, gateway):
        failing(gateway, SapNotReached("refused"))
        return client.post(URL, json=VALID_BODY).json()["id"]

    def test_the_users_own_order_is_found(self):
        client, gateway, _ = make()
        request_id = self.queued(client, gateway)
        body = client.get(f"{REQUESTS}/{request_id}").json()
        assert body["id"] == request_id and body["status"] == QUEUED
        assert set(body) == {"id", "status", "attempts", "created_at", "updated_at", "sales_order", "details", "message", "order"}

    def test_someone_elses_order_and_an_unknown_id_are_404(self):
        client, gateway, store = make()
        request_id = self.queued(client, gateway)
        other = TestClient(create_app(MockSalesOrderGateway(), Settings(jwt_secret=SECRET), store))
        other.cookies.set(ACCESS_TOKEN_COOKIE, token("user-2"))
        assert other.get(f"{REQUESTS}/{request_id}").status_code == 404
        assert client.get(f"{REQUESTS}/nope").status_code == 404

    def test_the_open_list_has_only_the_users_open_orders_newest_first(self):
        client, gateway, store = make()
        first, second = self.queued(client, gateway), self.queued(client, gateway)
        store.update(first, status="posted")
        third = self.queued(client, gateway)
        ids = [r["id"] for r in client.get(f"{REQUESTS}?open=true").json()["requests"]]
        assert ids == [third, second]

    def test_the_list_is_capped_at_50(self):
        client, gateway, _ = make()
        failing(gateway, SapNotReached("refused"))
        for _ in range(55):
            client.post(URL, json=VALID_BODY)
        assert len(client.get(REQUESTS).json()["requests"]) == 50

    def test_open_false_is_refused(self):
        assert make()[0].get(f"{REQUESTS}?open=false").status_code == 422

    @pytest.mark.parametrize("path", [REQUESTS, f"{REQUESTS}/abc"])
    def test_login_and_role_are_needed(self, path):
        assert make(roles=None)[0].get(path).status_code == 401
        assert make(roles=("management",))[0].get(path).status_code == 403

    def test_a_failing_store_is_503(self):
        client, _, store = make()
        store.db.close()
        assert client.get(REQUESTS).status_code == 503 and client.get(f"{REQUESTS}/abc").status_code == 503
