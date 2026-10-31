from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fastapi.testclient import TestClient
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from sami_agents.entrypoint.app import create_app
from sami_agents.infrastructure.mock_catalog_source import MockCatalogSource
from sami_agents.infrastructure.mock_relevance_checker import MockRelevanceChecker
from sami_agents.infrastructure.settings import Settings

SECRET = "s" * 32
URL = "/v1/agents/chat"


def token_with(roles: list[str]) -> str:
    payload = {"sub": "user-1", "sap_username": "SAP_USER", "roles": roles, "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    return jwt.encode(payload, SECRET, algorithm="HS256")


def make_client(roles=None, checker=None, source=None) -> TestClient:
    app = create_app(Settings(jwt_secret=SECRET, _env_file=None), checker or MockRelevanceChecker(), source or MockCatalogSource())
    client = TestClient(app)
    if roles is not None:
        client.cookies.set(ACCESS_TOKEN_COOKIE, token_with(roles))
    return client


class TestAccess:
    def test_no_cookie_is_401(self):
        assert make_client().post(URL, json={"message": "sales"}).status_code == 401

    def test_a_bad_token_is_401(self):
        client = make_client()
        client.cookies.set(ACCESS_TOKEN_COOKIE, "garbage")
        assert client.post(URL, json={"message": "sales"}).status_code == 401

    @pytest.mark.parametrize("roles", [["sales"], ["stores"]])
    def test_other_roles_are_403(self, roles):
        assert make_client(roles).post(URL, json={"message": "sales"}).status_code == 403

    @pytest.mark.parametrize("roles", [["management"], ["admin"]])
    def test_management_and_admin_pass(self, roles):
        assert make_client(roles).post(URL, json={"message": "sales"}).status_code == 200


class TestBody:
    @pytest.mark.parametrize("message", ["", "   ", "x" * 501])
    def test_an_empty_or_too_long_message_is_422(self, message):
        assert make_client(["management"]).post(URL, json={"message": message}).status_code == 422

    def test_a_missing_message_is_422(self):
        assert make_client(["management"]).post(URL, json={}).status_code == 422

    def test_the_longest_message_is_accepted(self):
        assert make_client(["management"]).post(URL, json={"message": "x" * 500}).status_code == 200


class TestAnswer:
    def test_returns_an_open_ui_program_as_plain_text(self):
        response = make_client(["management"]).post(URL, json={"message": "top customers"})
        assert response.headers["content-type"] == "text/plain; charset=utf-8"
        assert response.text == "\n".join(
            [
                "root = Stack([intro, w1, w2])",
                'intro = Text("Here is Top customers and Top materials.")',
                'w1 = Widget("top-customers")',
                'w2 = Widget("top-materials")',
            ]
        )

    def test_the_message_is_trimmed_before_it_reaches_the_checker(self):
        checker = MockRelevanceChecker()
        make_client(["management"], checker).post(URL, json={"message": "  top customers  "})
        assert {message for message, _ in checker.calls} == {"top customers"}

    def test_builder_returns_a_board(self):
        response = make_client(["management"]).post(URL, json={"message": "@builder top customers"})
        assert 'board = Board("Top Customers", ["top-customers", "top-materials"])' in response.text

    def test_a_widget_the_checker_rejects_is_left_out(self):
        response = make_client(["management"], MockRelevanceChecker({"top-materials": 0.0})).post(URL, json={"message": "top customers"})
        assert 'Widget("top-customers")' in response.text and "top-materials" not in response.text

    def test_a_checker_that_is_down_still_answers_from_the_keywords(self):
        response = make_client(["management"], MockRelevanceChecker(fail_from=0)).post(URL, json={"message": "top customers"})
        assert response.status_code == 200
        assert 'Widget("top-customers")' in response.text


class TestCatalog:
    def test_the_users_cookie_is_forwarded_to_the_catalog_source(self):
        source = MockCatalogSource()
        client = make_client(["management"], source=source)
        client.post(URL, json={"message": "sales"})
        assert source.tokens == [client.cookies[ACCESS_TOKEN_COOKIE]]

    def test_an_unavailable_catalog_is_503_in_the_error_shape(self):
        response = make_client(["management"], source=MockCatalogSource(unavailable=True)).post(URL, json={"message": "sales"})
        assert (response.status_code, response.json()) == (503, {"code": "CATALOG_UNAVAILABLE"})

    def test_responses_carry_a_request_id(self):
        assert make_client(["management"]).post(URL, json={"message": "sales"}).headers["x-request-id"]
