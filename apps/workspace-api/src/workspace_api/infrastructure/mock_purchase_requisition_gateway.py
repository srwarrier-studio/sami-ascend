from datetime import datetime, timezone
from decimal import Decimal

from workspace_api.domain.entities.purchase_requisition import (
    NewPurchaseRequisition,
    PurchaseRequisition,
    PurchaseRequisitionItem,
    PurchaseRequisitionPage,
)
from workspace_api.domain.errors import PurchaseRequisitionNotFound, PurchaseRequisitionRejected, ValidationDetail
from workspace_api.domain.gateways.purchase_requisition_gateway import PurchaseRequisitionGateway

PLANT_COMPANIES = {"1000": "INA1", "2000": "INA2", "3000": "INA3"}


class MockPurchaseRequisitionGateway(PurchaseRequisitionGateway):
    def __init__(self):
        self.requisitions: dict[str, PurchaseRequisition] = {}
        self.rejection: list[ValidationDetail] | None = None

    def reject_with(self, details: list[ValidationDetail]) -> None:
        self.rejection = details

    def create(self, requisition: NewPurchaseRequisition) -> PurchaseRequisition:
        if self.rejection:
            raise PurchaseRequisitionRejected(self.rejection)
        number = str(10000000 + len(self.requisitions))
        items = [
            PurchaseRequisitionItem(
                f"{(index + 1) * 10}", i.material, i.text or i.material, i.plant, PLANT_COMPANIES.get(i.plant, ""), i.quantity, i.unit,
                Decimal("0.00"), "INR", i.delivery_date, "not_released", "01", False, False, "",
            )
            for index, i in enumerate(requisition.items)
        ]
        now = datetime.now(timezone.utc).replace(microsecond=0)
        created = PurchaseRequisition(number, requisition.description, "MOCK", now.date(), now, items)
        self.requisitions[number] = created
        return created

    def list_recent(self, top: int, skip: int, companies: list[str]) -> PurchaseRequisitionPage:
        mine = sorted((r for r in self.requisitions.values() if r.company_codes & set(companies)), key=lambda r: r.purchase_requisition, reverse=True)
        return PurchaseRequisitionPage(mine[skip : skip + top], len(mine))

    def get(self, number: str) -> PurchaseRequisition:
        if number not in self.requisitions:
            raise PurchaseRequisitionNotFound(number)
        return self.requisitions[number]

    def release(self, number: str, release_code: str, item: str | None) -> PurchaseRequisition:
        raise PurchaseRequisitionRejected([ValidationDetail("RELEASE_REFUSED", "The mock does not release.", "release_code")])
