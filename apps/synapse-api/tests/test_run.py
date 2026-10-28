import pytest
from test_routes_totals import DAILY, make_client

from synapse_api.entrypoint import run
from synapse_api.infrastructure.mock_sales_source import MockSalesSource
from synapse_api.infrastructure.settings import Settings


class TestRequestId:
    def test_response_carries_a_request_id(self):
        response = make_client(MockSalesSource(DAILY), ["management"]).get("/v1/synapse/sales/today")
        assert response.headers["x-request-id"]

    def test_a_valid_incoming_request_id_is_kept(self):
        response = make_client(MockSalesSource(DAILY), ["management"]).get(
            "/v1/synapse/sales/today", headers={"X-Request-ID": "req-123"}
        )
        assert response.headers["x-request-id"] == "req-123"

    def test_error_responses_carry_a_request_id(self):
        response = make_client(MockSalesSource(DAILY)).get("/v1/synapse/sales/today")
        assert response.status_code == 401
        assert response.headers["x-request-id"]


class TestCors:
    def test_frontend_origin_is_allowed_with_credentials(self):
        response = make_client(MockSalesSource(DAILY), ["management"]).get(
            "/v1/synapse/sales/today", headers={"Origin": "http://localhost:5173"}
        )
        assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
        assert response.headers["access-control-allow-credentials"] == "true"

    def test_other_origin_is_not_allowed(self):
        response = make_client(MockSalesSource(DAILY), ["management"]).get(
            "/v1/synapse/sales/today", headers={"Origin": "http://evil.example"}
        )
        assert "access-control-allow-origin" not in response.headers


class TestRunner:
    def test_exits_when_jwt_secret_is_empty(self, monkeypatch):
        monkeypatch.setattr(run, "Settings", lambda: Settings(jwt_secret="", _env_file=None))
        with pytest.raises(SystemExit, match="JWT_SECRET"):
            run.main()
