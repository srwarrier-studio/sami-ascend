from abc import ABC, abstractmethod

from butterfly.domain.entities.production import ProductionConfirmation, WorkCenterDowntime


class ProductionRepo(ABC):
    @abstractmethod
    def confirmations(self) -> list[ProductionConfirmation]: ...

    @abstractmethod
    def downtimes(self) -> list[WorkCenterDowntime]: ...

    def listing(self, entity: str):
        return getattr(self, entity)()

    def summary_listing(self, name: str):
        return None
