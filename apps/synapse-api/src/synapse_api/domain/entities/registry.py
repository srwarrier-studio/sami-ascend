from dataclasses import dataclass, field


@dataclass(frozen=True)
class Dimension:
    name: str
    entity: str
    order: str
    key: str | None = None
    name_field: str | None = None
    unit: str | None = None
    quantity: str | None = None
    count: str | None = None


@dataclass(frozen=True)
class Metric:
    name: str
    label: str
    service: str
    measure: str
    date: str
    currency: str
    dimensions: dict[str, Dimension] = field(default_factory=dict)
    company: str | None = None


@dataclass(frozen=True)
class Interval:
    start: str
    end: str
    fallback: str
    open_to_today: bool


@dataclass(frozen=True)
class Delay:
    due: str
    done: str


@dataclass(frozen=True)
class RecordType:
    name: str
    service: str
    entity: str
    key_fields: tuple[str, ...]
    order: str
    interval: Interval | None = None
    delay: Delay | None = None
    company: str | None = None


@dataclass(frozen=True)
class Registry:
    metrics: dict[str, Metric]
    records: dict[str, RecordType]
