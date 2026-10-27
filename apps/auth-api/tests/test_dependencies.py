from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from token_verification import Role
from auth_api.entrypoint.dependencies import (
    ACCESS_TOKEN_COOKIE,
    current_claims,
    require_role,
    token_service,
)
from auth_api.infrastructure.mock.mock_user_repo import MOCK_USER

app = FastAPI()


@app.get("/who")
def who(claims=Depends(current_claims)):
    return claims.userid


@app.get("/stores-page", dependencies=[Depends(require_role(Role.STORES))])
def stores_page(): ...


@app.get("/accounts-page", dependencies=[Depends(require_role(Role.ACCOUNTS))])
def accounts_page(): ...


def logged_in_client() -> TestClient:
    client = TestClient(app)
    client.cookies.set(ACCESS_TOKEN_COOKIE, token_service.issue(MOCK_USER))
    return client


def test_no_cookie_is_401():
    assert TestClient(app).get("/who").status_code == 401


def test_garbage_cookie_is_401():
    client = TestClient(app)
    client.cookies.set(ACCESS_TOKEN_COOKIE, "garbage")

    assert client.get("/who").status_code == 401


def test_valid_cookie_identifies_user():
    response = logged_in_client().get("/who")

    assert response.json() == str(MOCK_USER.userid.value)


def test_role_in_token_can_open_its_page():
    assert logged_in_client().get("/stores-page").status_code == 200


def test_role_missing_from_token_is_403():
    response = logged_in_client().get("/accounts-page")

    assert response.status_code == 403
    assert response.json()["detail"] == "You are not allowed to view this page"
