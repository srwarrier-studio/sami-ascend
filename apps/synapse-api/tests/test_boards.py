from fastapi.testclient import TestClient
from test_routes_totals import DAILY, SECRET, TODAY, token_with
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from synapse_api.entrypoint.app import create_app
from synapse_api.infrastructure.mock_sales_source import MockSalesSource
from synapse_api.infrastructure.settings import Settings
from synapse_api.infrastructure.sqlite_board_store import SqliteBoardStore

BASE = "/v1/synapse/boards"
SALES = {"id": "w1", "catalogId": "sales-today"}
FINANCE = {"id": "w2", "catalogId": "fin-collections"}
PRODUCTION = {"id": "w3", "catalogId": "prod-output"}


def app_with(store):
    return create_app(MockSalesSource(DAILY), Settings(jwt_secret=SECRET, _env_file=None), lambda: TODAY, boards=store)


def as_user(store, user: str, roles: list[str]) -> TestClient:
    import jwt
    from datetime import datetime, timedelta, timezone

    payload = {"sub": user, "sap_username": user.upper(), "roles": roles, "companies": [], "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    client = TestClient(app_with(store))
    client.cookies.set(ACCESS_TOKEN_COOKIE, jwt.encode(payload, SECRET, algorithm="HS256"))
    return client


def make(store=None):
    store = store or SqliteBoardStore(":memory:")
    return store, as_user(store, "ann", ["management"]), as_user(store, "bob", ["production"])


class TestOwnBoards:
    def test_create_list_rename_save_delete(self):
        _, ann, _ = make()
        created = ann.post(BASE, json={"name": "Mine", "widgets": [SALES]})
        assert created.status_code == 201
        board_id = created.json()["id"]
        assert ann.patch(f"{BASE}/{board_id}", json={"name": "Renamed"}).json()["name"] == "Renamed"
        assert ann.put(f"{BASE}/{board_id}/widgets", json={"widgets": [SALES, FINANCE]}).json()["widgets"] == [{**SALES, "size": None}, {**FINANCE, "size": None}]
        assert [b["name"] for b in ann.get(BASE).json()] == ["Renamed"]
        assert ann.delete(f"{BASE}/{board_id}").status_code == 204
        assert ann.get(BASE).json() == []

    def test_a_fourth_board_is_refused(self):
        _, ann, _ = make()
        for _ in range(3):
            assert ann.post(BASE, json={"name": "b"}).status_code == 201
        assert ann.post(BASE, json={"name": "b"}).status_code == 409

    def test_boards_survive_a_restart(self, tmp_path):
        path = str(tmp_path / "boards.db")
        as_user(SqliteBoardStore(path), "ann", ["management"]).post(BASE, json={"name": "Kept"})
        assert [b["name"] for b in as_user(SqliteBoardStore(path), "ann", ["management"]).get(BASE).json()] == ["Kept"]

    def test_saving_a_widget_the_user_cannot_see_is_403(self):
        _, _, bob = make()
        response = bob.post(BASE, json={"name": "x", "widgets": [FINANCE]})
        assert response.status_code == 403 and response.json() == {"code": "WIDGET_NOT_ALLOWED"}

    def test_widgets_that_lost_access_are_hidden_but_kept(self):
        store, ann, bob = make()
        board_id = ann.post(BASE, json={"name": "Mixed", "widgets": [FINANCE, PRODUCTION]}).json()["id"]
        owner_as_bob = as_user(store, "ann", ["production"])
        assert [w["catalogId"] for w in owner_as_bob.get(BASE).json()[0]["widgets"]] == ["prod-output"]
        owner_as_bob.put(f"{BASE}/{board_id}/widgets", json={"widgets": [PRODUCTION]})
        assert [w["catalogId"] for w in ann.get(BASE).json()[0]["widgets"]] == ["prod-output", "fin-collections"]


class TestPrivacy:
    def test_other_users_do_not_see_a_private_board(self):
        _, ann, bob = make()
        board_id = ann.post(BASE, json={"name": "Secret", "widgets": [PRODUCTION]}).json()["id"]
        assert bob.get(BASE).json() == []
        assert bob.get(BASE + "/shared").json() == []
        assert bob.patch(f"{BASE}/{board_id}", json={"name": "x"}).status_code == 404
        assert bob.post(f"{BASE}/shared/{board_id}/copy").status_code == 404

    def test_a_non_owner_cannot_change_a_public_board(self):
        _, ann, bob = make()
        board_id = ann.post(BASE, json={"name": "Open", "isPublic": True, "widgets": [PRODUCTION]}).json()["id"]
        assert bob.patch(f"{BASE}/{board_id}", json={"name": "x"}).status_code == 403
        assert bob.put(f"{BASE}/{board_id}/widgets", json={"widgets": []}).status_code == 403
        assert bob.delete(f"{BASE}/{board_id}").status_code == 403


class TestShared:
    def test_a_public_board_is_listed_without_widgets_the_viewer_cannot_see(self):
        _, ann, bob = make()
        ann.post(BASE, json={"name": "Mixed", "isPublic": True, "widgets": [FINANCE, PRODUCTION]})
        listed = bob.get(BASE + "/shared").json()
        assert [(b["name"], b["owner"], b["shared"]) for b in listed] == [("Mixed", "ANN", True)]
        assert [w["catalogId"] for w in listed[0]["widgets"]] == ["prod-output"]

    def test_a_board_with_nothing_visible_is_not_listed(self):
        _, ann, bob = make()
        ann.post(BASE, json={"name": "Money", "isPublic": True, "widgets": [FINANCE]})
        assert bob.get(BASE + "/shared").json() == []

    def test_the_owner_does_not_see_their_own_board_as_shared(self):
        _, ann, _ = make()
        ann.post(BASE, json={"name": "Open", "isPublic": True, "widgets": [SALES]})
        assert ann.get(BASE + "/shared").json() == []

    def test_a_copy_is_private_independent_and_filtered(self):
        _, ann, bob = make()
        shared_id = ann.post(BASE, json={"name": "Mixed", "isPublic": True, "widgets": [FINANCE, PRODUCTION]}).json()["id"]
        copy = bob.post(f"{BASE}/shared/{shared_id}/copy")
        assert copy.status_code == 201 and copy.json()["isPublic"] is False and copy.json()["shared"] is False
        assert [w["catalogId"] for w in copy.json()["widgets"]] == ["prod-output"]
        ann.put(f"{BASE}/{shared_id}/widgets", json={"widgets": []})
        assert [w["catalogId"] for w in bob.get(BASE).json()[0]["widgets"]] == ["prod-output"]

    def test_copying_at_the_limit_is_409(self):
        _, ann, bob = make()
        shared_id = ann.post(BASE, json={"name": "Open", "isPublic": True, "widgets": [PRODUCTION]}).json()["id"]
        for _ in range(3):
            bob.post(BASE, json={"name": "b"})
        assert bob.post(f"{BASE}/shared/{shared_id}/copy").status_code == 409


class TestAccess:
    def test_signed_out_is_401(self):
        assert TestClient(app_with(SqliteBoardStore(":memory:"))).get(BASE).status_code == 401
