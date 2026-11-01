from butterfly.domain.entities.drivers import (
    CustomerInvoice,
    ProductionOrder,
    ProductionOrderComponent,
    PurchaseDelivery,
    SalesContract,
)
from butterfly.domain.repositories.driver_repo import DriverRepo


class InMemoryDriverRepo(DriverRepo):
    def __init__(
        self,
        contracts: list[SalesContract] | None = None,
        deliveries: list[PurchaseDelivery] | None = None,
        production_orders: list[ProductionOrder] | None = None,
        components: list[ProductionOrderComponent] | None = None,
        invoices: list[CustomerInvoice] | None = None,
    ):
        self._contracts = contracts or []
        self._deliveries = deliveries or []
        self._production_orders = production_orders or []
        self._components = components or []
        self._invoices = invoices or []

    def contracts(self) -> list[SalesContract]:
        return list(self._contracts)

    def deliveries(self) -> list[PurchaseDelivery]:
        return list(self._deliveries)

    def invoices(self) -> list[CustomerInvoice]:
        return list(self._invoices)

    def production_orders(self) -> list[ProductionOrder]:
        return list(self._production_orders)

    def components(self) -> list[ProductionOrderComponent]:
        return list(self._components)
