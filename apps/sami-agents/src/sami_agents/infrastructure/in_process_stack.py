from datetime import date, datetime, timedelta, timezone

import httpx
import jwt

SECRET = "s" * 32


class Forward(httpx.BaseTransport):
    def __init__(self, client):
        self.client = client

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        answer = self.client.get(str(request.url), headers=dict(request.headers))
        return httpx.Response(answer.status_code, json=answer.json())


def stack_for(scenario: str, today: date):
    from fastapi.testclient import TestClient

    from butterfly.entrypoint.app import build_default_app
    from butterfly.infrastructure.api.odata import DRIVERS_ROOT, ROOT
    from synapse_api.entrypoint.app import create_app
    from synapse_api.infrastructure.mock_sales_source import MockSalesSource
    from synapse_api.infrastructure.odata_reader import ODataReader
    from synapse_api.infrastructure.registry_metric_source import RegistryMetricSource
    from synapse_api.infrastructure.registry_record_source import RegistryRecordSource
    from synapse_api.infrastructure.settings import Settings as SynapseSettings

    from sami_agents.infrastructure.settings import Settings
    from sami_agents.infrastructure.synapse_data_source import SynapseDataSource

    butterfly = Forward(TestClient(build_default_app(today, "story", scenario)))
    readers = {
        "sales": ODataReader(f"http://testserver{ROOT}", 10, butterfly),
        "drivers": ODataReader(f"http://testserver{DRIVERS_ROOT}", 10, butterfly),
    }
    app = create_app(
        MockSalesSource(), SynapseSettings(jwt_secret=SECRET, _env_file=None), lambda: today,
        metrics=RegistryMetricSource(readers), records=RegistryRecordSource(readers),
    )
    source = SynapseDataSource(Settings(synapse_url="http://testserver", _env_file=None), Forward(TestClient(app)))
    payload = {"sub": "evaluator", "sap_username": "EVAL", "roles": ["management"], "exp": datetime.now(timezone.utc) + timedelta(minutes=30)}
    return source, jwt.encode(payload, SECRET, algorithm="HS256")
