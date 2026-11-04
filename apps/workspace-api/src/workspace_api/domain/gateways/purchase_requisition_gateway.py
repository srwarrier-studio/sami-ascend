from abc import ABC, abstractmethod

from workspace_api.domain.entities.purchase_requisition import (
    NewPurchaseRequisition,
    PurchaseRequisition,
    PurchaseRequisitionPage,
)


class PurchaseRequisitionGateway(ABC):
    @abstractmethod
    def create(self, requisition: NewPurchaseRequisition) -> PurchaseRequisition: ...

    @abstractmethod
    def list_recent(self, top: int, skip: int, companies: list[str]) -> PurchaseRequisitionPage: ...

    @abstractmethod
    def get(self, number: str) -> PurchaseRequisition: ...

    @abstractmethod
    def release(self, number: str, release_code: str, item: str | None) -> PurchaseRequisition: ...
