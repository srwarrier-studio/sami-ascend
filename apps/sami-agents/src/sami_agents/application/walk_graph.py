from dataclasses import dataclass, field
from datetime import date, timedelta

from sami_agents.application import anomaly_kinds
from sami_agents.domain.entities.finding import Hit, Related, Start, Step, Window, WalkResult
from sami_agents.domain.entities.graph import ANOMALY_KINDS, Anomaly, Edge, Graph, Node
from sami_agents.domain.errors import DataUnavailable
from sami_agents.domain.gateways.data_source import DataSource

MAX_DEPTH = 6
MAX_VISITS = 100
MAX_CALLS = 200
MAX_READ_DAYS = 400
MODES = ("root_cause", "impact", "dependency")


@dataclass
class Run:
    source: DataSource
    token: str
    today: date
    calls: int = 0
    seen: set = field(default_factory=set)
    truncated: bool = False

    def allowed(self, lookup: tuple) -> bool:
        if lookup in self.seen:
            return False
        if len(self.seen) >= MAX_VISITS or self.calls >= MAX_CALLS:
            self.truncated = True
            return False
        self.seen.add(lookup)
        self.calls += 1
        return True


@dataclass
class Context:
    node: str
    rows: list[dict]
    path: tuple[Step, ...]
    window: Window
    kind: str | None = None
    last_at: date | None = None
    carried: frozenset[str] | None = None
    visited: frozenset[str] = frozenset()


class WalkGraph:
    def __init__(self, graph: Graph, source: DataSource):
        self.graph = graph
        self.source = source

    def execute(self, mode: str, starts: list[Start], window: Window, token: str, today: date) -> WalkResult:
        if mode not in MODES:
            raise ValueError(f"mode must be one of {', '.join(MODES)}")
        run = Run(self.source, token, today)
        result = WalkResult()
        for start in starts:
            if start.node not in self.graph.nodes:
                raise ValueError(f"unknown node '{start.node}'")
            if mode == "dependency":
                self.depend(run, start, window, result)
            else:
                self.trace(run, mode, start, window, result)
        result.truncated = run.truncated
        return result

    def trace(self, run: Run, mode: str, start: Start, window: Window, result: WalkResult) -> None:
        node = self.graph.nodes[start.node]
        rows = self.start_rows(run, node, start, window)
        if mode == "root_cause":
            result.paths += self.walk(run, mode, Context(node.name, rows, (), window, visited=frozenset({node.name})))
            return
        leaving = {kind for edge in self.graph.edges.values() if edge.cause == node.name for kind in edge.carries}
        tested = [a for a in node.anomalies if a.kind in leaving]
        if node.id and start.key_field == node.id:
            tested = [a for a in tested if ANOMALY_KINDS[a.kind]["per_row"]]
        for key, hit, hit_rows in self.hits(run, node, start.key_field or "", [start.key], {start.key: rows}, window, tested):
            step = Step(node.name, None, start.key_field or "key", key, hit.kind, hit.at, hit.numbers, hit.rows)
            context = Context(node.name, hit_rows, (step,), window, hit.kind, hit.at, frozenset({hit.kind}), frozenset({node.name}))
            deeper = self.walk(run, mode, context)
            result.paths += deeper or [(step,)]

    def start_rows(self, run: Run, node: Node, start: Start, window: Window) -> list[dict]:
        if node.source_kind == "metric":
            return [{"key": start.key}]
        if not start.key_field:
            raise ValueError(f"start on record node '{node.name}' needs a key_field")
        if not run.allowed((node.name, start.key_field, start.key)):
            return []
        return run.source.records(run.token, node.source, start.key_field, start.key, window.start, window.end)

    def walk(self, run: Run, mode: str, context: Context) -> list[tuple[Step, ...]]:
        if len(context.path) >= MAX_DEPTH:
            run.truncated = True
            return []
        found: list[tuple[Step, ...]] = []
        root = mode == "root_cause"
        for edge in self.graph.edges.values():
            if (edge.effect if root else edge.cause) != context.node:
                continue
            node = self.graph.nodes[edge.cause if root else edge.effect]
            if node.name in context.visited:
                continue
            carried = frozenset(edge.carries) or context.carried
            if not root and carried is not None and context.kind not in carried:
                continue
            if root and edge.shows and context.kind is not None and context.kind not in edge.shows:
                continue
            found += self.hop(run, mode, context, edge, node, carried)
        return found

    def hop(self, run: Run, mode: str, context: Context, edge: Edge, node: Node, carried: frozenset[str] | None) -> list[tuple[Step, ...]]:
        root = mode == "root_cause"
        from_field, to_field = (edge.effect_field, edge.cause_field) if root else (edge.cause_field, edge.effect_field)
        values = sorted({str(row[from_field]) for row in context.rows if row.get(from_field) not in (None, "")})
        window = context.window
        if not node.passthrough:
            window = window.widened_back(edge.lookback_days) if root else window.widened_forward(edge.lookback_days, run.today)
        tested = [] if node.passthrough else self.tested(node, root, carried, edge)
        rows_by_value = self.read(run, node, to_field, values, window, tested)
        visited = context.visited | {node.name}
        if node.passthrough:
            rows = [row for rows in rows_by_value.values() for row in rows]
            return self.walk(run, mode, Context(node.name, rows, context.path, window, context.kind, context.last_at, carried, visited)) if rows else []
        found = []
        for keys, hit, hit_rows in self.hits(run, node, to_field, values, rows_by_value, window, tested):
            if not self.in_order(root, hit.at, context.last_at):
                continue
            step = Step(node.name, edge.name, to_field, keys, hit.kind, hit.at, hit.numbers, hit.rows)
            deeper = self.walk(run, mode, Context(node.name, hit_rows, (*context.path, step), window, hit.kind, hit.at or context.last_at, frozenset({hit.kind}), visited))
            found += deeper or [(*context.path, step)]
        return found

    def tested(self, node: Node, root: bool, carried: frozenset[str] | None, edge: Edge) -> list[Anomaly]:
        if not root:
            return [a for a in node.anomalies if a.kind in edge.shows]
        if carried is None:
            return list(node.anomalies)
        return [a for a in node.anomalies if a.kind in carried]

    def in_order(self, root: bool, at: date | None, last_at: date | None) -> bool:
        if at is None or last_at is None:
            return True
        return at <= last_at if root else at >= last_at

    def read(self, run: Run, node: Node, field_name: str, values: list[str], window: Window, tested: list[Anomaly]) -> dict[str, list[dict]]:
        if node.source_kind == "metric":
            return {value: [{"key": value}] for value in values}
        start, end = self.read_range(window, tested)
        rows: dict[str, list[dict]] = {}
        for value in values:
            if run.allowed((node.name, field_name, value)):
                rows[value] = run.source.records(run.token, node.source, field_name, value, start, end)
        return rows

    def read_range(self, window: Window, tested: list[Anomaly]) -> tuple[date, date]:
        pads = [a.params["pad_days"] for a in tested if a.kind in ("sum_changed", "set_changed")]
        start, end = window.span(max(pads)) if pads else (window.start, window.end)
        return max(start, end - timedelta(days=MAX_READ_DAYS - 1)), end

    def hits(self, run: Run, node: Node, field_name: str, values: list[str], rows_by_value: dict[str, list[dict]], window: Window, tested: list[Anomaly]) -> list[tuple[tuple[str, ...], Hit, list[dict]]]:
        found: list[tuple[tuple[str, ...], Hit, list[dict]]] = []
        for anomaly in tested:
            params = anomaly.params
            if anomaly.kind == "value_changed":
                for value in values:
                    if not run.allowed((node.name, "change", value)):
                        continue
                    change = run.source.member_change(run.token, node.source, node.dimension, value, window)
                    found += [((value,), hit, [{"key": value}]) for hit in anomaly_kinds.value_changed(change, params)]
            elif anomaly.kind in ("sum_changed", "set_changed"):
                every = [row for value in values for row in rows_by_value.get(value, [])]
                grouped = getattr(anomaly_kinds, anomaly.kind)(every, params, window)
                found += [(tuple(values), hit, hit.rows) for hit in grouped]
            else:
                for value in values:
                    if value not in rows_by_value:
                        continue
                    rows = rows_by_value[value]
                    hits = anomaly_kinds.later_than(rows, params, run.today) if anomaly.kind == "later_than" else anomaly_kinds.coverage_gap(rows, params, window)
                    found += [((value,), hit, hit.rows) for hit in hits]
        return found

    def depend(self, run: Run, start: Start, window: Window, result: WalkResult) -> None:
        node = self.graph.nodes[start.node]
        wide = Window.before(window.end - timedelta(days=MAX_READ_DAYS - 1), window.end)
        queue = [(node, self.start_rows(run, node, start, wide), 0)]
        while queue:
            current, rows, depth = queue.pop(0)
            if depth >= MAX_DEPTH:
                run.truncated = True
                continue
            for edge in self.graph.edges.values():
                for side in ("cause", "effect"):
                    if getattr(edge, side) != current.name:
                        continue
                    other = self.graph.nodes[edge.effect if side == "cause" else edge.cause]
                    from_field, to_field = (edge.cause_field, edge.effect_field) if side == "cause" else (edge.effect_field, edge.cause_field)
                    values = sorted({str(row[from_field]) for row in rows if row.get(from_field) not in (None, "")})
                    for value, found in self.read(run, other, to_field, values, wide, []).items():
                        if found and (other.name, "related", value) not in run.seen:
                            run.seen.add((other.name, "related", value))
                            result.related.append(Related(other.name, to_field, value, len(found)))
                            queue.append((other, found, depth + 1))
