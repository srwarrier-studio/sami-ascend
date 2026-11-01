from datetime import date

from synapse_api.domain.entities.registry import RecordType
from synapse_api.domain.errors import SapUnavailable
from synapse_api.domain.gateways.record_source import RecordSource


class MockRecordSource(RecordSource):
    def __init__(self, rows: dict[str, list[dict]] | None = None):
        self.stored = rows or {}
        self.failing = False
        self.calls = 0

    def for_companies(self, companies: tuple[str, ...]) -> "MockRecordSource":
        return self

    def fail(self) -> None:
        self.failing = True

    def rows(self, record: RecordType, key_field: str, key: str, end: date | None) -> list[dict]:
        self.calls += 1
        if self.failing:
            raise SapUnavailable()
        return [row for row in self.stored.get(record.name, []) if row[key_field] == key]
