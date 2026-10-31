import tomllib
from pathlib import Path

from synapse_api.domain.entities.registry import Delay, Dimension, Interval, Metric, RecordType, Registry

SERVICES = ("sales", "drivers")
METRIC_KEYS = {"label", "service", "measure", "date", "currency", "by"}
DIMENSION_KEYS = {"entity", "order", "key", "name", "unit", "quantity", "count"}
RECORD_KEYS = {"service", "entity", "key_fields", "order", "interval", "delay"}
INTERVAL_KEYS = {"from", "to", "fallback", "open_to_today"}
DELAY_KEYS = {"due", "done"}


class RegistryError(Exception): ...


def load_registry(path: Path) -> Registry:
    try:
        data = tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise RegistryError(f"registry {path.name}: {error}") from error
    unknown = set(data) - {"metric", "record"}
    if unknown:
        raise RegistryError(f"registry: unknown section {sorted(unknown)[0]}")
    metrics = {name: build_metric(name, body) for name, body in data.get("metric", {}).items()}
    records = {name: build_record(name, body) for name, body in data.get("record", {}).items()}
    return Registry(metrics, records)


def text(body: dict, key: str, where: str) -> str:
    value = body.get(key)
    if not isinstance(value, str) or not value:
        raise RegistryError(f"registry: {where} needs '{key}' as text")
    return value


def optional_text(body: dict, key: str, where: str) -> str | None:
    return text(body, key, where) if key in body else None


def only(body: dict, allowed: set[str], where: str) -> None:
    extra = set(body) - allowed
    if extra:
        raise RegistryError(f"registry: {where} has unknown key '{sorted(extra)[0]}'")


def service_of(body: dict, where: str) -> str:
    service = text(body, "service", where)
    if service not in SERVICES:
        raise RegistryError(f"registry: {where} has unknown service '{service}' (use {' or '.join(SERVICES)})")
    return service


def build_metric(name: str, body: dict) -> Metric:
    where = f"metric '{name}'"
    only(body, METRIC_KEYS, where)
    by = body.get("by")
    if not isinstance(by, dict) or "day" not in by:
        raise RegistryError(f"registry: {where} needs a 'by.day' entity for totals")
    dimensions = {dimension: build_dimension(dimension, spec, where) for dimension, spec in by.items()}
    return Metric(
        name, text(body, "label", where), service_of(body, where), text(body, "measure", where),
        text(body, "date", where), text(body, "currency", where), dimensions,
    )


def build_dimension(name: str, body: dict, metric_where: str) -> Dimension:
    where = f"{metric_where} dimension '{name}'"
    if not isinstance(body, dict):
        raise RegistryError(f"registry: {where} must be a table")
    only(body, DIMENSION_KEYS, where)
    key = optional_text(body, "key", where)
    label = optional_text(body, "name", where)
    if name != "day" and (key is None or label is None):
        raise RegistryError(f"registry: {where} needs 'key' and 'name'")
    return Dimension(
        name, text(body, "entity", where), text(body, "order", where), key, label,
        optional_text(body, "unit", where), optional_text(body, "quantity", where), optional_text(body, "count", where),
    )


def build_record(name: str, body: dict) -> RecordType:
    where = f"record '{name}'"
    only(body, RECORD_KEYS, where)
    key_fields = body.get("key_fields")
    if not isinstance(key_fields, list) or not key_fields or not all(isinstance(k, str) and k for k in key_fields):
        raise RegistryError(f"registry: {where} needs 'key_fields' as a list of text")
    interval = build_interval(body["interval"], where) if "interval" in body else None
    delay = build_delay(body["delay"], where) if "delay" in body else None
    return RecordType(
        name, service_of(body, where), text(body, "entity", where), tuple(key_fields), text(body, "order", where), interval, delay
    )


def build_interval(body: dict, record_where: str) -> Interval:
    where = f"{record_where} interval"
    only(body, INTERVAL_KEYS, where)
    start, end = text(body, "from", where), text(body, "to", where)
    open_to_today = body.get("open_to_today", False)
    if not isinstance(open_to_today, bool):
        raise RegistryError(f"registry: {where} needs 'open_to_today' as true or false")
    return Interval(start, end, optional_text(body, "fallback", where) or end, open_to_today)


def build_delay(body: dict, record_where: str) -> Delay:
    where = f"{record_where} delay"
    only(body, DELAY_KEYS, where)
    return Delay(text(body, "due", where), text(body, "done", where))
