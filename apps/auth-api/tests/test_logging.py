import logging
from unittest.mock import patch

from fastapi.testclient import TestClient

with patch("auth_api.infrastructure.interface.msal_auth_provider.MSALAuthProvider"):
    from auth_api.entrypoint.app import app


def test_request_gets_an_id_and_an_access_log_line(caplog):
    with caplog.at_level(logging.INFO, logger="access"):
        response = TestClient(app).get("/v1/auth/me")

    assert len(response.headers["x-request-id"]) == 36
    assert any(r.getMessage().startswith("GET /v1/auth/me 401") for r in caplog.records)
