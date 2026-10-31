import uuid
from dataclasses import dataclass
from datetime import datetime, timezone

from workspace_api.domain.entities.order_request import QUEUED, UNKNOWN, OrderRequest
from workspace_api.domain.entities.sales_order import NewSalesOrder, SalesOrder
from workspace_api.domain.errors import SapNotReached, SapOutcomeUnknown
from workspace_api.domain.gateways.sales_order_gateway import SalesOrderGateway
from workspace_api.domain.repositories.order_request_store import OrderRequestStore
from workspace_api.infrastructure.order_json import order_to_dict

QUEUED_MESSAGE = "SAP could not take the order right now. It is saved and will be sent automatically."
UNKNOWN_MESSAGE = "We could not confirm that SAP received the order. Check the order list before entering it again."


@dataclass(frozen=True)
class Submitter:
    user: str
    sap_username: str
    request_id: str | None


class CreateSalesOrder:
    def __init__(self, gateway: SalesOrderGateway, store: OrderRequestStore | None = None):
        self.gateway = gateway
        self.store = store

    def execute(self, order: NewSalesOrder, submitter: Submitter | None = None) -> SalesOrder | OrderRequest:
        try:
            return self.gateway.create(order)
        except (SapNotReached, SapOutcomeUnknown) as error:
            if self.store is None or submitter is None:
                raise
            kept = self.keep(order, submitter, QUEUED if isinstance(error, SapNotReached) else UNKNOWN)
            self.store.add(kept)
            return kept

    def keep(self, order: NewSalesOrder, submitter: Submitter, status: str) -> OrderRequest:
        now = datetime.now(timezone.utc)
        message = QUEUED_MESSAGE if status == QUEUED else UNKNOWN_MESSAGE
        return OrderRequest(
            uuid.uuid4().hex, submitter.user, submitter.sap_username, submitter.request_id, order_to_dict(order),
            status, 0, now, now, now, message=message,
        )
