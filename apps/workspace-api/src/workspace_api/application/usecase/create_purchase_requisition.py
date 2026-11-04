from workspace_api.domain.entities.purchase_requisition import NewPurchaseRequisition, PurchaseRequisition
from workspace_api.domain.errors import CompanyNotAllowed
from workspace_api.domain.gateways.purchase_requisition_gateway import PurchaseRequisitionGateway


class CreatePurchaseRequisition:
    def __init__(self, gateway: PurchaseRequisitionGateway, plants_by_company: dict[str, tuple[str, ...]]):
        self.gateway = gateway
        self.plants_by_company = plants_by_company

    def execute(self, requisition: NewPurchaseRequisition, companies: list[str]) -> PurchaseRequisition:
        for item in requisition.items:
            owner = next((code for code, plants in self.plants_by_company.items() if item.plant in plants), item.plant)
            if owner not in companies:
                raise CompanyNotAllowed(owner)
        return self.gateway.create(requisition)
