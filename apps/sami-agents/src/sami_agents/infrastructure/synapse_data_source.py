from datetime import date
from decimal import Decimal

import httpx
from structured_logging import get_request_id
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from sami_agents.domain.entities.finding import MemberChange, Window
from sami_agents.domain.errors import DataUnavailable
from sami_agents.domain.gateways.data_source import DataSource
from sami_agents.infrastructure.settings import Settings

TOP = 50


def decimal_of(value: str | None) -> Decimal | None:
    return Decimal(value) if value is not None else None


class SynapseDataSource(DataSource):
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.client = httpx.Client(base_url=settings.synapse_url, timeout=settings.model_timeout_seconds, transport=transport)

    def records(self, token: str, record_type: str, key_field: str, key: str, start: date | None, end: date | None) -> list[dict]:
        params = {"type": record_type, "key": key, "key_field": key_field}
        if start and end:
            params |= {"start": start.isoformat(), "end": end.isoformat()}
        return self.get(token, "/v1/synapse/records", params)["records"]

    def member_change(self, token: str, metric: str, dimension: str, key: str, window: Window) -> MemberChange | None:
        params = {
            "start": window.start.isoformat(), "end": window.end.isoformat(),
            "compare_start": window.compare_start.isoformat(), "compare_end": window.compare_end.isoformat(),
            "by": dimension, "top": TOP,
        }
        for comparison in self.get(token, f"/v1/synapse/metrics/{metric}/compare", params)["comparisons"]:
            for row in comparison["rows"]:
                if row["key"] == key:
                    return MemberChange(
                        Decimal(row["current"]), Decimal(row["previous"]), self.percent(row),
                        decimal_of(row.get("volume_effect")), decimal_of(row.get("price_effect")),
                    )
        return None

    def percent(self, row: dict) -> Decimal | None:
        previous = Decimal(row["previous"])
        return ((Decimal(row["current"]) - previous) / previous * 100).quantize(Decimal("0.01")) if previous else None

    def get(self, token: str, path: str, params: dict) -> dict:
        headers = {"Cookie": f"{ACCESS_TOKEN_COOKIE}={token}"}
        if request_id := get_request_id():
            headers["X-Request-ID"] = request_id
        try:
            response = self.client.get(path, params=params, headers=headers)
        except httpx.TransportError as error:
            raise DataUnavailable(type(error).__name__) from error
        if response.status_code != 200:
            raise DataUnavailable(f"unexpected status {response.status_code}")
        try:
            return response.json()
        except ValueError as error:
            raise DataUnavailable("unreadable body") from error
