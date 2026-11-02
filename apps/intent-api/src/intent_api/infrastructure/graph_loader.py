import tomllib
from pathlib import Path
from typing import Any

from intent_api.domain.entities.graph import ANOMALY_KINDS, DEFAULT_LOOKBACK_DAYS, Anomaly, Edge, Graph, Node
from intent_api.domain.errors import GraphError

NODE_KEYS = {"source", "anomaly", "passthrough", "id", "label"}
EDGE_KEYS = {"cause", "effect", "join", "carries", "shows", "lookback_days"}


def load_graph(path: Path) -> Graph:
    try:
        data = tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise GraphError([f"graph {path.name}: {error}"]) from error
    problems: list[str] = []
    for section in set(data) - {"node", "edge"}:
        problems.append(f"graph: unknown section '{section}'")
    nodes = {name: build_node(name, body, problems) for name, body in data.get("node", {}).items()}
    edges = {name: build_edge(name, body, problems) for name, body in data.get("edge", {}).items()}
    for edge in edges.values():
        for end in (edge.cause, edge.effect):
            if end and end not in nodes:
                problems.append(f"edge '{edge.name}': unknown node '{end}'")
    if problems:
        raise GraphError(problems)
    return Graph(nodes, edges)


def is_text(value: Any) -> bool:
    return isinstance(value, str) and bool(value)


def is_number(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def build_node(name: str, body: Any, problems: list[str]) -> Node:
    where = f"node '{name}'"
    if not isinstance(body, dict):
        problems.append(f"{where}: must be a table")
        return Node(name, "", "")
    for key in set(body) - NODE_KEYS:
        problems.append(f"{where}: unknown key '{key}'")
    source_kind, source, dimension = parse_source(body.get("source"), where, problems)
    passthrough = body.get("passthrough", False)
    if not isinstance(passthrough, bool):
        problems.append(f"{where}: 'passthrough' must be true or false")
        passthrough = False
    node_id = body.get("id")
    if node_id is not None and not is_text(node_id):
        problems.append(f"{where}: 'id' must be a field name as text")
        node_id = None
    label = body.get("label")
    if label is not None and not is_text(label):
        problems.append(f"{where}: 'label' must be text")
        label = None
    raw = body.get("anomaly", [])
    entries = [raw] if isinstance(raw, dict) else raw
    if not isinstance(entries, list):
        problems.append(f"{where}: 'anomaly' must be a table or a list of tables")
        entries = []
    anomalies = tuple(build_anomaly(entry, where, problems) for entry in entries)
    return Node(name, source_kind, source, dimension, anomalies, passthrough, node_id, label)


def parse_source(text: Any, where: str, problems: list[str]) -> tuple[str, str, str | None]:
    if not is_text(text) or ":" not in text:
        problems.append(f"{where}: 'source' must look like record:<type> or metric:<metric>.<dimension>")
        return "", "", None
    kind, _, rest = text.partition(":")
    if kind == "record" and rest:
        return kind, rest, None
    if kind == "metric" and rest.count(".") == 1 and all(rest.split(".")):
        metric, dimension = rest.split(".")
        return kind, metric, dimension
    problems.append(f"{where}: 'source' must look like record:<type> or metric:<metric>.<dimension>, not '{text}'")
    return "", "", None


def build_anomaly(entry: Any, where: str, problems: list[str]) -> Anomaly:
    if not isinstance(entry, dict) or entry.get("kind") not in ANOMALY_KINDS:
        problems.append(f"{where}: anomaly kind must be one of {', '.join(ANOMALY_KINDS)}, not '{entry.get('kind') if isinstance(entry, dict) else entry}'")
        return Anomaly("", {})
    kind = entry["kind"]
    spec = ANOMALY_KINDS[kind]
    here = f"{where} anomaly '{kind}'"
    params: dict[str, Any] = {}
    allowed = {"kind", *spec["text"], *spec["optional"], *spec["numbers"]}
    for key in set(entry) - allowed:
        problems.append(f"{here}: unknown parameter '{key}'")
    for name in spec["text"]:
        if not is_text(entry.get(name)):
            problems.append(f"{here}: needs '{name}' as text")
        params[name] = entry.get(name)
    for name in spec["optional"]:
        if name in entry and not is_text(entry[name]):
            problems.append(f"{here}: '{name}' must be text")
        params[name] = entry.get(name)
    for name, default in spec["numbers"].items():
        value = entry.get(name, default)
        if value is None:
            problems.append(f"{here}: needs '{name}' as a number")
        elif not is_number(value) or value < 0:
            problems.append(f"{here}: '{name}' must be a number from 0 up")
        params[name] = value
    return Anomaly(kind, params)


def build_edge(name: str, body: Any, problems: list[str]) -> Edge:
    where = f"edge '{name}'"
    if not isinstance(body, dict):
        problems.append(f"{where}: must be a table")
        return Edge(name, "", "", "", "")
    for key in set(body) - EDGE_KEYS:
        problems.append(f"{where}: unknown key '{key}'")
    for key in ("cause", "effect"):
        if not is_text(body.get(key)):
            problems.append(f"{where}: needs '{key}' as text")
    join = body.get("join")
    if not isinstance(join, dict) or set(join) != {"cause", "effect"} or not all(is_text(v) for v in join.values()):
        problems.append(f"{where}: 'join' needs 'cause' and 'effect' field names as text")
        join = {"cause": "", "effect": ""}
    lists = {}
    for key in ("carries", "shows"):
        value = body.get(key, [])
        if not isinstance(value, list) or not all(is_text(k) for k in value):
            problems.append(f"{where}: '{key}' must be a list of anomaly kinds")
            value = []
        lists[key] = tuple(value)
    lookback = body.get("lookback_days", DEFAULT_LOOKBACK_DAYS)
    if not isinstance(lookback, int) or isinstance(lookback, bool) or lookback < 0:
        problems.append(f"{where}: 'lookback_days' must be a whole number from 0 up")
        lookback = DEFAULT_LOOKBACK_DAYS
    return Edge(name, body.get("cause") or "", body.get("effect") or "", join["cause"], join["effect"], lists["carries"], lists["shows"], lookback)
