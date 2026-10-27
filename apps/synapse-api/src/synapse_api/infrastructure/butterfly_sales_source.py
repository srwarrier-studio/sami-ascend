from collections.abc import Callable
from datetime import date
from decimal import Decimal

import httpx
from structured_logging import get_request_id

from synapse_api.domain.entities.sales import CustomerSales, DailySales, HighValueOrder, MaterialSales
from synapse_api.domain.errors import SapUnavailable
from synapse_api.domain.gateways.sales_source import SalesSource
from synapse_api.infrastructure.butterfly_sales_mapper import (
    customer_from_json,
    daily_from_json,
    material_from_json,
)
from synapse_api.infrastructure.settings import Settings


class ButterflySalesSource(SalesSource):
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.client = httpx.Client(
            base_url=settings.sap_base_url,
            timeout=settings.sap_timeout_seconds,
            transport=transport,
        )

    def daily_sales(self, start: date, end: date) -> list[DailySales]:
        return self.summary("SalesSummaryByDay", start, end, daily_from_json)

    def customer_sales(self, start: date, end: date) -> list[CustomerSales]:
        return self.summary("SalesSummaryByCustomer", start, end, customer_from_json)

    def material_sales(self, start: date, end: date) -> list[MaterialSales]:
        return self.summary("SalesSummaryByMaterial", start, end, material_from_json)

    def high_value_orders(self, minimum: Decimal, top: int) -> list[HighValueOrder]:
        raise NotImplementedError

    def summary(self, entity: str, start: date, end: date, to_row: Callable[[dict], object]) -> list:
        filter_ = f"OrderDate%20ge%20{start.isoformat()}%20and%20OrderDate%20le%20{end.isoformat()}"
        return [to_row(row) for row in self.get_rows(f"{entity}?$filter={filter_}&$orderby=OrderDate")]

    def get_rows(self, path: str) -> list[dict]:
        headers = {"Accept": "application/json"}
        if request_id := get_request_id():
            headers["X-Request-ID"] = request_id
        try:
            response = self.client.get(path, headers=headers)
        except httpx.TransportError as error:
            raise SapUnavailable(type(error).__name__) from error
        if response.status_code != 200:
            raise SapUnavailable(f"unexpected status {response.status_code}")
        try:
            return response.json()["value"]
        except (ValueError, KeyError, TypeError) as error:
            raise SapUnavailable("unreadable body") from error
