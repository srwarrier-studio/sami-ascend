from workspace_api.application.usecase.get_purchase_requisition import GetPurchaseRequisition
from workspace_api.domain.entities.purchase_requisition import PurchaseRequisition
from workspace_api.domain.gateways.purchase_requisition_gateway import PurchaseRequisitionGateway


class ReleasePurchaseRequisition:
    def __init__(self, gateway: PurchaseRequisitionGateway):
        self.gateway = gateway

    def execute(self, number: str, companies: list[str], release_code: str, item: str | None) -> PurchaseRequisition:
        GetPurchaseRequisition(self.gateway).execute(number, companies)
        return self.gateway.release(number, release_code, item)
