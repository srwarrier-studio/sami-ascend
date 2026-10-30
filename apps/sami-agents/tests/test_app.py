import pytest
from fastapi.testclient import TestClient

from sami_agents.entrypoint import run
from sami_agents.entrypoint.app import create_app
from sami_agents.infrastructure.settings import Settings

SECRET = "test-secret-with-enough-length-32bytes"


def make_client() -> TestClient:
    return TestClient(create_app(Settings(jwt_secret=SECRET, _env_file=None)))


class TestHealth:
    def test_answers_ok_without_a_login(self):
        response = make_client().get("/v1/agents/health")
        assert (response.status_code, response.json()) == (200, {"status": "ok"})


class TestRequestId:
    def test_response_carries_a_request_id(self):
        assert make_client().get("/v1/agents/health").headers["x-request-id"]

    def test_a_valid_incoming_request_id_is_kept(self):
        response = make_client().get("/v1/agents/health", headers={"X-Request-ID": "req-123"})
        assert response.headers["x-request-id"] == "req-123"


class TestCors:
    def test_frontend_origin_is_allowed_with_credentials(self):
        response = make_client().get("/v1/agents/health", headers={"Origin": "http://localhost:5173"})
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
        assert response.headers["access-control-allow-credentials"] == "true"

    def test_other_origin_is_not_allowed(self):
        response = make_client().get("/v1/agents/health", headers={"Origin": "http://evil.example"})
        assert "access-control-allow-origin" not in response.headers


class TestSettings:
    def test_defaults_point_at_local_ollama_and_synapse_api(self):
        settings = Settings(_env_file=None)
        assert settings.ollama_url == "http://localhost:11434"
        assert settings.ollama_model == "gemma3:270m"
        assert settings.synapse_url == "http://localhost:8004"
        assert settings.model_timeout_seconds == 20

    def test_environment_overrides_the_model(self, monkeypatch):
        monkeypatch.setenv("OLLAMA_MODEL", "lfm2.5-1.2b")
        assert Settings(_env_file=None).ollama_model == "lfm2.5-1.2b"


class TestRunner:
    def test_exits_when_jwt_secret_is_empty(self, monkeypatch):
        monkeypatch.setattr(run, "Settings", lambda: Settings(jwt_secret="", _env_file=None))
        with pytest.raises(SystemExit, match="JWT_SECRET"):
            run.main()
