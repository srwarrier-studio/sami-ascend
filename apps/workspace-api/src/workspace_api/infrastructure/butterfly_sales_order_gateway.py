import httpx
from structured_logging import get_request_id

from workspace_api.domain.entities.sales_order import NewSalesOrder, SalesOrder, SalesOrderPage
from workspace_api.domain.errors import SalesOrderRejected, SapUnavailable, ValidationDetail
from workspace_api.domain.gateways.sales_order_gateway import SalesOrderGateway
from workspace_api.infrastructure.butterfly_order_mapper import new_order_to_json, order_from_json
from workspace_api.infrastructure.settings import Settings


class ButterflySalesOrderGateway(SalesOrderGateway):
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.client = httpx.Client(
            base_url=settings.sap_base_url,
            timeout=settings.sap_timeout_seconds,
            transport=transport,
        )

    def create(self, order: NewSalesOrder) -> SalesOrder:
        response = self.send("POST", "SalesOrder", json=new_order_to_json(order))
        if response.status_code == 400:
            raise SalesOrderRejected(details_from(response))
        if response.status_code != 201:
            raise SapUnavailable(f"unexpected status {response.status_code}")
        return order_from_json(response.json())

    def list_recent(self, top: int, skip: int) -> SalesOrderPage:
        query = f"$orderby=SalesOrder%20desc&$top={top}&$skip={skip}&$count=true&$expand=_Item"
        response = self.send("GET", f"SalesOrder?{query}")
        if response.status_code != 200:
            raise SapUnavailable(f"unexpected status {response.status_code}")
        body = response.json()
        return SalesOrderPage([order_from_json(row) for row in body["value"]], body["@odata.count"])

    def send(self, method: str, path: str, **kwargs) -> httpx.Response:
        headers = {"Accept": "application/json"}
        if request_id := get_request_id():
            headers["X-Request-ID"] = request_id
        try:
            response = self.client.request(method, path, headers=headers, **kwargs)
        except httpx.TransportError as error:
            raise SapUnavailable(type(error).__name__) from error
        if response.status_code >= 500:
            raise SapUnavailable(f"status {response.status_code}")
        return response


def details_from(response: httpx.Response) -> list[ValidationDetail]:
    try:
        raw = response.json()["error"]["details"]
        return [ValidationDetail(d["code"], d["message"], d["target"]) for d in raw]
    except (ValueError, KeyError, TypeError) as error:
        raise SapUnavailable("unreadable 400 body") from error
