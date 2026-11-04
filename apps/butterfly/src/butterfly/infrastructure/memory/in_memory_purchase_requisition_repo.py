from butterfly.domain.entities.purchase_requisition import PurchaseRequisition
from butterfly.domain.repositories.purchase_requisition_repo import FIRST_NUMBER, PurchaseRequisitionRepo


class InMemoryPurchaseRequisitionRepo(PurchaseRequisitionRepo):
    def __init__(self, requisitions: list[PurchaseRequisition] | None = None):
        self.requisitions = {requisition.purchase_requisition: requisition for requisition in requisitions or []}

    def list_all(self) -> list[PurchaseRequisition]:
        return list(self.requisitions.values())

    def get(self, purchase_requisition: str) -> PurchaseRequisition | None:
        return self.requisitions.get(purchase_requisition)

    def next_number(self) -> str:
        return str(max((int(number) for number in self.requisitions), default=FIRST_NUMBER - 1) + 1)

    def add(self, requisition: PurchaseRequisition) -> None:
        self.requisitions[requisition.purchase_requisition] = requisition

    def update(self, requisition: PurchaseRequisition) -> None:
        self.requisitions[requisition.purchase_requisition] = requisition
