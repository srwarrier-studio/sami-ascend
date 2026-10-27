from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from token_verification import Role, TokenVerifier
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE, AuthDependencies

SECRET = "s" * 32
auth = AuthDependencies(TokenVerifier(SECRET))
app = FastAPI()


@app.get("/who")
def who(claims=Depends(auth.current_claims)):
    return claims.userid


@app.get("/stores-page", dependencies=[Depends(auth.require_roles(Role.STORES))])
def stores_page(): ...


@app.get("/accounts-page", dependencies=[Depends(auth.require_roles(Role.ACCOUNTS))])
def accounts_page(): ...


def client_with_cookie(token: str) -> TestClient:
    client = TestClient(app)
    client.cookies.set(ACCESS_TOKEN_COOKIE, token)
    return client


def valid_token() -> str:
    payload = {
        "sub": "user-1",
        "sap_username": "SAP_READONLY",
        "roles": ["stores"],
        "exp": datetime.now(timezone.utc) + timedelta(minutes=5),
    }
    return jwt.encode(payload, SECRET, algorithm="HS256")


def test_no_cookie_is_401():
    assert TestClient(app).get("/who").status_code == 401


def test_garbage_cookie_is_401():
    assert client_with_cookie("garbage").get("/who").status_code == 401


def test_valid_cookie_identifies_user():
    assert client_with_cookie(valid_token()).get("/who").json() == "user-1"


def test_role_in_token_can_open_its_page():
    assert client_with_cookie(valid_token()).get("/stores-page").status_code == 200


def test_role_missing_from_token_is_403():
    response = client_with_cookie(valid_token()).get("/accounts-page")

    assert response.status_code == 403
    assert response.json()["detail"] == "You are not allowed to view this page"
