from datetime import date
from typing import Any

from pydantic import BaseModel

from synapse_api.domain.entities.registry import RecordType


class RecordsResponse(BaseModel):
    type: str
    key_field: str
    key: str
    start: date | None
    end: date | None
    records: list[dict[str, Any]]


class RecordTypeResponse(BaseModel):
    name: str
    key_fields: list[str]
    takes_window: bool
    has_delay_days: bool


class RecordTypesResponse(BaseModel):
    types: list[RecordTypeResponse]

    @classmethod
    def from_domain(cls, types: list[RecordType]) -> "RecordTypesResponse":
        return cls(
            types=[
                RecordTypeResponse(name=t.name, key_fields=list(t.key_fields), takes_window=t.interval is not None, has_delay_days=t.delay is not None)
                for t in types
            ]
        )
