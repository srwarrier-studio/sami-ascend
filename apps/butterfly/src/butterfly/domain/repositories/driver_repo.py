from abc import ABC, abstractmethod

from butterfly.domain.entities.drivers import (
    CustomerInvoice,
    ProductionOrder,
    ProductionOrderComponent,
    PurchaseDelivery,
    SalesContract,
)


class DriverRepo(ABC):
    def listing(self, entity: str):
        return getattr(self, entity)()

    @abstractmethod
    def contracts(self) -> list[SalesContract]: ...

    @abstractmethod
    def deliveries(self) -> list[PurchaseDelivery]: ...

    @abstractmethod
    def invoices(self) -> list[CustomerInvoice]: ...

    @abstractmethod
    def production_orders(self) -> list[ProductionOrder]: ...

    @abstractmethod
    def components(self) -> list[ProductionOrderComponent]: ...
