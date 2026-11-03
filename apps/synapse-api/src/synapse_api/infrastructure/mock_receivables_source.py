from datetime import date

from synapse_api.domain.entities.receivables import AgeBucket, CustomerReceivable, ReceivablesTotal
from synapse_api.domain.gateways.receivables_source import ReceivablesSource


class MockReceivablesSource(ReceivablesSource):
    def __init__(self, totals: list[ReceivablesTotal] | None = None, customers: list[CustomerReceivable] | None = None, buckets: list[AgeBucket] | None = None):
        self._totals = totals or []
        self.customers = customers or []
        self.buckets = buckets or []

    def for_companies(self, companies: tuple[str, ...]) -> "MockReceivablesSource":
        return self

    def totals(self, as_of: date) -> list[ReceivablesTotal]:
        return self._totals

    def by_customer(self, as_of: date) -> list[CustomerReceivable]:
        return self.customers

    def ageing(self, as_of: date) -> list[AgeBucket]:
        return self.buckets
