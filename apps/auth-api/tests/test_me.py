from unittest.mock import patch

import pytest

from fastapi.testclient import TestClient

from token_verification import Company
from auth_api.entrypoint.dependencies import ACCESS_TOKEN_COOKIE, token_service
from auth_api.infrastructure.mock.mock_user_repo import MOCK_USER

with patch("auth_api.infrastructure.interface.msal_auth_provider.MSALAuthProvider"):
    from auth_api.entrypoint.app import app


@pytest.fixture(autouse=True)
def mock_users(monkeypatch):
    from auth_api.entrypoint import app as app_module
    from auth_api.infrastructure.mock.mock_unit_of_work import MockAuthUnitOfWork

    monkeypatch.setattr(app_module, "uow", MockAuthUnitOfWork())


def me_for(companies):
    MOCK_USER.companies = companies
    client = TestClient(app)
    client.cookies.set(ACCESS_TOKEN_COOKIE, token_service.issue(MOCK_USER))
    MOCK_USER.companies = []
    return client.get("/v1/auth/me")


def test_me_returns_the_users_companies():
    response = me_for([Company.SABINSA, Company.ORGANICA])

    assert response.status_code == 200
    assert response.json()["companies"] == ["sabinsa", "organica"]


def test_user_without_companies_gets_an_empty_list():
    response = me_for([])

    assert response.status_code == 200
    assert response.json()["companies"] == []


def test_a_disabled_user_is_refused_at_me():
    MOCK_USER.disabled = True
    try:
        client = TestClient(app)
        client.cookies.set(ACCESS_TOKEN_COOKIE, token_service.issue(MOCK_USER))
        assert client.get("/v1/auth/me").status_code == 401
    finally:
        MOCK_USER.disabled = False
