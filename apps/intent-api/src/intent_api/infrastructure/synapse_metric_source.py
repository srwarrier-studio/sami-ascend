from datetime import date
from decimal import Decimal

import httpx
from structured_logging import get_request_id
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from intent_api.domain.entities.figures import Comparison, MonthFigure, Row, TrendPoint, Window
from intent_api.domain.errors import MetricsUnavailable
from intent_api.domain.gateways.metric_source import MetricSource
from intent_api.infrastructure.settings import Settings

OTHER = "other"


def decimal_of(value) -> Decimal | None:
    return Decimal(value) if value is not None else None


class SynapseMetricSource(MetricSource):
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.client = httpx.Client(base_url=settings.synapse_url, timeout=settings.synapse_timeout_seconds, transport=transport)

    def month(self, token: str, metric: str, month: date, trend: int) -> list[MonthFigure]:
        body = self.get(token, f"/v1/synapse/metrics/{metric}/month", {"month": month.strftime("%Y-%m"), "trend": trend})
        try:
            return [
                MonthFigure(
                    figure["currency"], Decimal(figure["net_amount"]), decimal_of(figure["previous_change_percent"]), figure["complete"],
                    tuple(TrendPoint(point["year"], point["month"], Decimal(point["net_amount"])) for point in figure["trend"]),
                )
                for figure in body["figures"]
            ]
        except (KeyError, TypeError, ArithmeticError) as error:
            raise MetricsUnavailable("unreadable body") from error

    def compare(self, token: str, metric: str, window: Window, by: str | None, top: int) -> list[Comparison]:
        params = {
            "start": window.start.isoformat(), "end": window.end.isoformat(),
            "compare_start": window.compare_start.isoformat(), "compare_end": window.compare_end.isoformat(),
            "top": top,
        }
        if by:
            params["by"] = by
        body = self.get(token, f"/v1/synapse/metrics/{metric}/compare", params)
        try:
            return [self.comparison(entry) for entry in body["comparisons"]]
        except (KeyError, TypeError, ArithmeticError) as error:
            raise MetricsUnavailable("unreadable body") from error

    def comparison(self, entry: dict) -> Comparison:
        rows = entry["rows"] or []
        kept = tuple(Row(row["key"], row["name"], Decimal(row["current"]), Decimal(row["previous"])) for row in rows if row["key"] != OTHER)
        return Comparison(
            entry["currency"], Decimal(entry["current"]), Decimal(entry["previous"]), Decimal(entry["change"]),
            decimal_of(entry["change_percent"]), kept, len(kept) < len(rows),
        )

    def get(self, token: str, path: str, params: dict) -> dict:
        headers = {"Cookie": f"{ACCESS_TOKEN_COOKIE}={token}"}
        if request_id := get_request_id():
            headers["X-Request-ID"] = request_id
        try:
            response = self.client.get(path, params=params, headers=headers)
        except httpx.TransportError as error:
            raise MetricsUnavailable(type(error).__name__) from error
        if response.status_code != 200:
            raise MetricsUnavailable(f"unexpected status {response.status_code}")
        try:
            return response.json()
        except ValueError as error:
            raise MetricsUnavailable("unreadable body") from error
