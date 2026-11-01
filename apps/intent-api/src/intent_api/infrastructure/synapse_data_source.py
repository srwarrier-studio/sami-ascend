from datetime import date
from decimal import Decimal

import httpx
from structured_logging import get_request_id
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from intent_api.domain.analysis.finding import MemberChange, Window
from intent_api.domain.analysis.measure import Comparison, DimensionInfo, MetricInfo, MoverRow, TrendPoint
from intent_api.domain.errors import DataUnavailable
from intent_api.domain.analysis.data_source import DataSource
from intent_api.infrastructure.settings import Settings

TOP = 50


def decimal_of(value: str | None) -> Decimal | None:
    return Decimal(value) if value is not None else None


class SynapseDataSource(DataSource):
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None, company: str | None = None, client: httpx.Client | None = None):
        self.settings = settings
        self.transport = transport
        self.company = company
        self.client = client or httpx.Client(base_url=settings.synapse_url, timeout=settings.synapse_timeout_seconds, transport=transport)

    def for_company(self, company: str | None) -> "SynapseDataSource":
        return SynapseDataSource(self.settings, self.transport, company, self.client)

    def records(self, token: str, record_type: str, key_field: str, key: str, start: date | None, end: date | None) -> list[dict]:
        params = {"type": record_type, "key": key, "key_field": key_field}
        if start and end:
            params |= {"start": start.isoformat(), "end": end.isoformat()}
        return self.get(token, "/v1/synapse/records", params)["records"]

    def member_change(self, token: str, metric: str, dimension: str, key: str, window: Window) -> MemberChange | None:
        for comparison in self.compare(token, metric, window, dimension, TOP):
            for row in comparison.rows or []:
                if row.key == key:
                    return MemberChange(row.current, row.previous, self.percent(row.current, row.previous), row.volume_effect, row.price_effect)
        return None

    def metrics(self, token: str) -> list[MetricInfo]:
        body = self.get(token, "/v1/synapse/metrics", {})
        return [
            MetricInfo(m["name"], m["label"], tuple(DimensionInfo(d["name"], d["splits_volume_and_price"]) for d in m["dimensions"]))
            for m in body["metrics"]
        ]

    def compare(self, token: str, metric: str, window: Window, by: str | None, top: int) -> list[Comparison]:
        params = {
            "start": window.start.isoformat(), "end": window.end.isoformat(),
            "compare_start": window.compare_start.isoformat(), "compare_end": window.compare_end.isoformat(),
            "top": top,
        }
        if by:
            params["by"] = by
        body = self.get(token, f"/v1/synapse/metrics/{metric}/compare", params)
        return [
            Comparison(
                c["currency"], Decimal(c["current"]), Decimal(c["previous"]), Decimal(c["change"]), decimal_of(c["change_percent"]),
                None if c["rows"] is None else [self.mover(row) for row in c["rows"]],
            )
            for c in body["comparisons"]
        ]

    def mover(self, row: dict) -> MoverRow:
        return MoverRow(
            row["key"], row["name"], Decimal(row["current"]), Decimal(row["previous"]), Decimal(row["change"]),
            decimal_of(row["share_of_change_percent"]), row.get("unit"), decimal_of(row.get("volume_effect")), decimal_of(row.get("price_effect")),
        )

    def trend(self, token: str, metric: str, month: date, months: int) -> list[TrendPoint]:
        body = self.get(token, f"/v1/synapse/metrics/{metric}/month", {"month": month.strftime("%Y-%m"), "trend": months})
        if not body["figures"]:
            return []
        return [TrendPoint(f"{t['year']}-{t['month']:02d}", Decimal(t["net_amount"])) for t in body["figures"][0]["trend"]]

    def percent(self, current: Decimal, previous: Decimal) -> Decimal | None:
        return ((current - previous) / previous * 100).quantize(Decimal("0.01")) if previous else None

    def get(self, token: str, path: str, params: dict) -> dict:
        headers = {"Cookie": f"{ACCESS_TOKEN_COOKIE}={token}"}
        if self.company:
            params = {**params, "company": self.company}
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
