from datetime import date

from synapse_api.domain.entities.registry import RecordType
from synapse_api.domain.gateways.record_source import RecordSource
from synapse_api.infrastructure.odata_reader import ODataReader


class RegistryRecordSource(RecordSource):
    def __init__(self, readers: dict[str, ODataReader]):
        self.readers = readers

    def rows(self, record: RecordType, key_field: str, key: str, end: date | None) -> list[dict]:
        filter_ = f"{key_field}%20eq%20'{key}'"
        if record.interval and end:
            filter_ += f"%20and%20{record.interval.start}%20le%20{end.isoformat()}"
        return self.readers[record.service].all_rows(f"{record.entity}?$filter={filter_}&$orderby={record.order}")
