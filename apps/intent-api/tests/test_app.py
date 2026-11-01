import pytest
from fastapi.testclient import TestClient

from intent_api.entrypoint import run
from intent_api.entrypoint.app import create_app
from intent_api.infrastructure.settings import Settings

SECRET = "test-secret-with-enough-length-32bytes"


def make_client() -> TestClient:
    return TestClient(create_app(Settings(jwt_secret=SECRET, _env_file=None)))


class TestHealth:
    def test_answers_ok_without_a_login(self):
        response = make_client().get("/v1/intent/health")
        assert (response.status_code, response.json()) == (200, {"status": "ok"})


class TestRequestId:
    def test_response_carries_a_request_id(self):
        assert make_client().get("/v1/intent/health").headers["x-request-id"]


class TestCors:
    def test_frontend_origin_is_allowed_with_credentials(self):
        response = make_client().get("/v1/intent/health", headers={"Origin": "http://localhost:5173"})
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
        assert response.headers["access-control-allow-credentials"] == "true"

    def test_other_origin_is_not_allowed(self):
        response = make_client().get("/v1/intent/health", headers={"Origin": "http://evil.example"})
        assert "access-control-allow-origin" not in response.headers


class TestRunner:
    def test_exits_when_jwt_secret_is_empty(self, monkeypatch):
        monkeypatch.setattr(run, "Settings", lambda: Settings(jwt_secret="", _env_file=None))
        with pytest.raises(SystemExit, match="JWT_SECRET"):
            run.main()
