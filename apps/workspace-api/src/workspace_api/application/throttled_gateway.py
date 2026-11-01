import threading

from workspace_api.domain.entities.sales_order import NewSalesOrder, SalesOrder, SalesOrderPage
from workspace_api.domain.errors import SapBusy
from workspace_api.domain.gateways.sales_order_gateway import SalesOrderGateway


class ThrottledGateway(SalesOrderGateway):
    def __init__(self, gateway: SalesOrderGateway, limit: int, wait_seconds: float):
        self.gateway = gateway
        self.slots = threading.BoundedSemaphore(limit)
        self.wait_seconds = wait_seconds

    def create(self, order: NewSalesOrder) -> SalesOrder:
        if not self.slots.acquire(timeout=self.wait_seconds):
            raise SapBusy("no free write slot")
        try:
            return self.gateway.create(order)
        finally:
            self.slots.release()

    def list_recent(self, top: int, skip: int, companies: list[str]) -> SalesOrderPage:
        return self.gateway.list_recent(top, skip, companies)
