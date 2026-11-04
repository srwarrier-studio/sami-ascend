import httpx
from structured_logging import get_request_id

from workspace_api.domain.entities.purchase_requisition import NewPurchaseRequisition, PurchaseRequisition, PurchaseRequisitionPage
from workspace_api.domain.errors import (
    PurchaseRequisitionNotFound,
    PurchaseRequisitionRejected,
    SapNotReached,
    SapOutcomeUnknown,
    SapUnavailable,
    ValidationDetail,
)
from workspace_api.domain.gateways.purchase_requisition_gateway import PurchaseRequisitionGateway
from workspace_api.infrastructure.butterfly_requisition_mapper import (
    new_requisition_to_json,
    requisition_from_json,
    target_from_json,
)
from workspace_api.infrastructure.settings import Settings

LIST_LIMIT = 1000
EXPAND = "$expand=_PurchaseRequisitionItem"


class ButterflyPurchaseRequisitionGateway(PurchaseRequisitionGateway):
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None):
        self.service = httpx.Client(base_url=settings.sap_requisition_url, timeout=settings.sap_timeout_seconds, transport=transport)
        self.release_client = httpx.Client(base_url=settings.sap_release_url, timeout=settings.sap_timeout_seconds, transport=transport)

    def create(self, requisition: NewPurchaseRequisition) -> PurchaseRequisition:
        response = self.send(self.service, "POST", "PurchaseReqn", json=new_requisition_to_json(requisition))
        if response.status_code == 400:
            raise PurchaseRequisitionRejected(details_from(response))
        if response.status_code != 201:
            raise SapUnavailable(f"unexpected status {response.status_code}")
        return requisition_from_json(response.json())

    def list_recent(self, top: int, skip: int, companies: list[str]) -> PurchaseRequisitionPage:
        response = self.send(self.service, "GET", f"PurchaseReqn?$orderby=PurchaseRequisition%20desc&$top={LIST_LIMIT}&{EXPAND}")
        if response.status_code != 200:
            raise SapUnavailable(f"unexpected status {response.status_code}")
        mine = [r for r in map(requisition_from_json, response.json()["value"]) if r.company_codes & set(companies)]
        return PurchaseRequisitionPage(mine[skip : skip + top], len(mine))

    def get(self, number: str) -> PurchaseRequisition:
        response = self.send(self.service, "GET", f"PurchaseReqn('{number}')?{EXPAND}")
        if response.status_code == 404:
            raise PurchaseRequisitionNotFound(number)
        if response.status_code != 200:
            raise SapUnavailable(f"unexpected status {response.status_code}")
        return requisition_from_json(response.json())

    def release(self, number: str, release_code: str, item: str | None) -> PurchaseRequisition:
        body = {"ReleaseCode": release_code} | ({"PurchaseRequisitionItem": item} if item else {})
        response = self.send(self.release_client, "POST", f"{number}/release", json=body)
        if response.status_code == 404:
            raise PurchaseRequisitionNotFound(number)
        if response.status_code == 400:
            raise PurchaseRequisitionRejected(details_from(response))
        if response.status_code != 200:
            raise SapUnavailable(f"unexpected status {response.status_code}")
        return self.get(number)

    def send(self, client: httpx.Client, method: str, path: str, **kwargs) -> httpx.Response:
        headers = {"Accept": "application/json"}
        if request_id := get_request_id():
            headers["X-Request-ID"] = request_id
        try:
            response = client.request(method, path, headers=headers, **kwargs)
        except (httpx.ConnectError, httpx.ConnectTimeout, httpx.PoolTimeout) as error:
            raise SapNotReached(type(error).__name__) from error
        except httpx.TransportError as error:
            raise SapOutcomeUnknown(type(error).__name__) from error
        if response.status_code in (429, 503):
            raise SapNotReached(f"status {response.status_code}")
        if response.status_code >= 500:
            raise SapOutcomeUnknown(f"status {response.status_code}")
        return response


def details_from(response: httpx.Response) -> list[ValidationDetail]:
    try:
        raw = response.json()["error"]["details"]
        return [ValidationDetail(d["code"], d["message"], target_from_json(d["target"])) for d in raw]
    except (ValueError, KeyError, TypeError) as error:
        raise SapUnavailable("unreadable 400 body") from error
