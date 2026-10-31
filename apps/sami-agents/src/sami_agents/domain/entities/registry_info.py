from dataclasses import dataclass, field


@dataclass(frozen=True)
class RecordInfo:
    entity: str
    key_fields: tuple[str, ...]


@dataclass(frozen=True)
class RegistryInfo:
    metrics: dict[str, set[str]] = field(default_factory=dict)
    records: dict[str, RecordInfo] = field(default_factory=dict)
