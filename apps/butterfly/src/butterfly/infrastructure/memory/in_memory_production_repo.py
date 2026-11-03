from butterfly.domain.entities.production import ProductionConfirmation, WorkCenterDowntime
from butterfly.domain.repositories.production_repo import ProductionRepo


class InMemoryProductionRepo(ProductionRepo):
    def __init__(self, confirmations: list[ProductionConfirmation] | None = None, downtimes: list[WorkCenterDowntime] | None = None):
        self._confirmations = confirmations or []
        self._downtimes = downtimes or []

    def confirmations(self) -> list[ProductionConfirmation]:
        return list(self._confirmations)

    def downtimes(self) -> list[WorkCenterDowntime]:
        return list(self._downtimes)
