from workspace_api.domain.entities.purchase_requisition import PurchaseRequisition
from workspace_api.domain.errors import PurchaseRequisitionNotFound
from workspace_api.domain.gateways.purchase_requisition_gateway import PurchaseRequisitionGateway


class GetPurchaseRequisition:
    def __init__(self, gateway: PurchaseRequisitionGateway):
        self.gateway = gateway

    def execute(self, number: str, companies: list[str]) -> PurchaseRequisition:
        requisition = self.gateway.get(number)
        if not requisition.company_codes & set(companies):
            raise PurchaseRequisitionNotFound(number)
        return requisition
