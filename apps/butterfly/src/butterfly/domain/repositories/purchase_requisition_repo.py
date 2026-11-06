from abc import ABC, abstractmethod

from butterfly.domain.entities.purchase_requisition import PurchaseRequisition


class PurchaseRequisitionRepo(ABC):
    @abstractmethod
    def list_all(self) -> list[PurchaseRequisition]: ...

    @abstractmethod
    def get(self, purchase_requisition: str) -> PurchaseRequisition | None: ...

    @abstractmethod
    def next_number(self) -> str: ...

    @abstractmethod
    def add(self, requisition: PurchaseRequisition) -> None: ...

    @abstractmethod
    def update(self, requisition: PurchaseRequisition) -> None: ...
