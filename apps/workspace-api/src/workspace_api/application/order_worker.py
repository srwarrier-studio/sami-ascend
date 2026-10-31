from datetime import datetime, timedelta, timezone

from workspace_api.domain.entities.order_request import FAILED, POSTED, QUEUED, REJECTED, UNKNOWN
from workspace_api.domain.errors import SalesOrderRejected, SapBusy, SapNotReached
from workspace_api.domain.gateways.sales_order_gateway import SalesOrderGateway
from workspace_api.domain.repositories.order_request_store import OrderRequestStore
from workspace_api.infrastructure.order_json import order_from_dict

FIRST_WAIT_SECONDS = 30
LONGEST_WAIT_SECONDS = 900
BUSY_WAIT_SECONDS = 5
UNKNOWN_MESSAGE = "We could not confirm that SAP received the order. Check the order list before entering it again."


def backoff_seconds(attempts: int) -> int:
    return min(LONGEST_WAIT_SECONDS, FIRST_WAIT_SECONDS * 2 ** (attempts - 1))


class OrderWorker:
    def __init__(self, store: OrderRequestStore, gateway: SalesOrderGateway, max_attempts: int, clock=lambda: datetime.now(timezone.utc)):
        self.store = store
        self.gateway = gateway
        self.max_attempts = max_attempts
        self.clock = clock

    def run_once(self) -> bool:
        now = self.clock()
        request = self.store.claim_due(now)
        if request is None:
            return False
        try:
            created = self.gateway.create(order_from_dict(request.body))
        except SalesOrderRejected as rejected:
            details = [{"code": d.code, "target": d.target, "message": d.message} for d in rejected.details]
            self.store.update(request.id, status=REJECTED, details=details, message="SAP rejected the order.")
        except SapBusy:
            self.store.update(request.id, status=QUEUED, next_attempt_at=now + timedelta(seconds=BUSY_WAIT_SECONDS))
        except SapNotReached:
            attempts = request.attempts + 1
            if attempts >= self.max_attempts:
                self.store.update(request.id, status=FAILED, attempts=attempts, message="SAP could not take the order after several tries.")
            else:
                self.store.update(request.id, status=QUEUED, attempts=attempts, next_attempt_at=now + timedelta(seconds=backoff_seconds(attempts)))
        except Exception:
            self.store.update(request.id, status=UNKNOWN, message=UNKNOWN_MESSAGE)
        else:
            self.store.update(request.id, status=POSTED, sales_order=created.sales_order, message=None)
        return True
