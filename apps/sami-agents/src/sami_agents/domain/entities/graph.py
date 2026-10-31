from dataclasses import dataclass, field
from typing import Any

ANOMALY_KINDS: dict[str, dict[str, Any]] = {
    "later_than": {"text": ("due", "done"), "optional": ("reason",), "numbers": {"min_days": 3}, "explains": True, "per_row": True},
    "coverage_gap": {"text": ("from", "to"), "optional": (), "numbers": {}, "explains": True, "per_row": True},
    "sum_changed": {"text": ("field", "date"), "optional": (), "numbers": {"min_percent": None, "pad_days": 30}, "explains": False, "per_row": False},
    "value_changed": {"text": (), "optional": (), "numbers": {"min_percent": None}, "explains": False, "per_row": False},
    "set_changed": {"text": ("field", "date"), "optional": (), "numbers": {"pad_days": 30}, "explains": True, "per_row": False},
}
DEFAULT_LOOKBACK_DAYS = 60


@dataclass(frozen=True)
class Anomaly:
    kind: str
    params: dict[str, Any]


@dataclass(frozen=True)
class Node:
    name: str
    source_kind: str
    source: str
    dimension: str | None = None
    anomalies: tuple[Anomaly, ...] = ()
    passthrough: bool = False
    id: str | None = None


@dataclass(frozen=True)
class Edge:
    name: str
    cause: str
    effect: str
    cause_field: str
    effect_field: str
    carries: tuple[str, ...] = ()
    shows: tuple[str, ...] = ()
    lookback_days: int = DEFAULT_LOOKBACK_DAYS


@dataclass(frozen=True)
class Graph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: dict[str, Edge] = field(default_factory=dict)
