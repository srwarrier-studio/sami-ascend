from workspace_api.application.usecase.list_sales_orders import MAX_TOP
from workspace_api.domain.entities.purchase_requisition import PurchaseRequisitionPage
from workspace_api.domain.errors import InvalidQuery
from workspace_api.domain.gateways.purchase_requisition_gateway import PurchaseRequisitionGateway


class ListPurchaseRequisitions:
    def __init__(self, gateway: PurchaseRequisitionGateway):
        self.gateway = gateway

    def execute(self, companies: list[str], top: int = 20, skip: int = 0) -> PurchaseRequisitionPage:
        if not 1 <= top <= MAX_TOP:
            raise InvalidQuery(f"top must be between 1 and {MAX_TOP}")
        if skip < 0:
            raise InvalidQuery("skip must be 0 or more")
        if not companies:
            return PurchaseRequisitionPage([], 0)
        return self.gateway.list_recent(top, skip, companies)
