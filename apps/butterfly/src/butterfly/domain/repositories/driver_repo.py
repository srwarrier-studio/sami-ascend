from abc import ABC, abstractmethod

from butterfly.domain.entities.drivers import (
    ProductionOrder,
    ProductionOrderComponent,
    PurchaseDelivery,
    SalesContract,
)


class DriverRepo(ABC):
    @abstractmethod
    def contracts(self) -> list[SalesContract]: ...

    @abstractmethod
    def deliveries(self) -> list[PurchaseDelivery]: ...

    @abstractmethod
    def production_orders(self) -> list[ProductionOrder]: ...

    @abstractmethod
    def components(self) -> list[ProductionOrderComponent]: ...
