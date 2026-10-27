from workspace_api.domain.entities.sales_order import SalesOrderPage
from workspace_api.domain.gateways.sales_order_gateway import SalesOrderGateway

MAX_TOP = 100


class ListSalesOrders:
    def __init__(self, gateway: SalesOrderGateway):
        self.gateway = gateway

    def execute(self, top: int = 20, skip: int = 0) -> SalesOrderPage:
        if not 1 <= top <= MAX_TOP:
            raise ValueError(f"top must be between 1 and {MAX_TOP}")
        if skip < 0:
            raise ValueError("skip must be 0 or more")
        return self.gateway.list_recent(top, skip)
