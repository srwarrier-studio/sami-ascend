from workspace_api.domain.entities.sales_order import NewSalesOrder, SalesOrder
from workspace_api.domain.gateways.sales_order_gateway import SalesOrderGateway


class CreateSalesOrder:
    def __init__(self, gateway: SalesOrderGateway):
        self.gateway = gateway

    def execute(self, order: NewSalesOrder) -> SalesOrder:
        return self.gateway.create(order)
