import re
from datetime import date

from synapse_api.application.compare_metric import check_period
from synapse_api.domain.entities.registry import Registry
from synapse_api.domain.errors import InvalidQuery, RecordTypeNotFound
from synapse_api.domain.gateways.record_source import RecordSource

KEY = re.compile(r"[A-Za-z0-9_-]{1,40}")


def day_of(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


class ReadRecords:
    def __init__(self, source: RecordSource, registry: Registry):
        self.source = source
        self.registry = registry

    def execute(
        self, type_name: str, key: str, key_field: str | None, start: date | None, end: date | None, today: date
    ) -> tuple[str, list[dict]]:
        record = self.registry.records.get(type_name)
        if record is None:
            raise RecordTypeNotFound()
        field = key_field or record.key_fields[0]
        if field not in record.key_fields or not KEY.fullmatch(key):
            raise InvalidQuery()
        if record.interval is None:
            return field, self.ordered(record, [self.with_delay(record, row, today) for row in self.source.rows(record, field, key, None)])
        if start is None or end is None:
            raise InvalidQuery()
        check_period(start, end)
        rows = self.source.rows(record, field, key, end)
        kept = [row for row in rows if self.overlaps(record, row, start, end, today)]
        return field, self.ordered(record, [self.with_delay(record, row, today) for row in kept])

    def overlaps(self, record, row: dict, start: date, end: date, today: date) -> bool:
        interval = record.interval
        first = day_of(row[interval.start])
        last = day_of(row[interval.end]) or day_of(row[interval.fallback]) or first
        if row[interval.end] is None and interval.open_to_today:
            last = max(last, today)
        low, high = min(first, last), max(first, last)
        return low <= end and high >= start

    def with_delay(self, record, row: dict, today: date) -> dict:
        if record.delay is None:
            return row
        due = day_of(row[record.delay.due])
        done = day_of(row[record.delay.done]) or today
        return {**row, "delay_days": max(0, (done - due).days)}

    def ordered(self, record, rows: list[dict]) -> list[dict]:
        fields = record.order.split(",")
        return sorted(rows, key=lambda row: [row.get(f) or "" for f in fields])
