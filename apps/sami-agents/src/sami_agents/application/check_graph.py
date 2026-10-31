from sami_agents.domain.entities.graph import Graph, Node
from sami_agents.domain.entities.registry_info import RegistryInfo

FIELD_PARAMS = ("due", "done", "from", "to", "field", "date", "reason")
RECORD_KINDS = {"later_than", "coverage_gap", "sum_changed", "set_changed"}
METRIC_KINDS = {"value_changed"}


class CheckGraph:
    def __init__(self, registry: RegistryInfo, contracts: dict[str, list[str]]):
        self.registry = registry
        self.contracts = contracts

    def execute(self, graph: Graph) -> tuple[list[str], list[str]]:
        problems: list[str] = []
        for node in graph.nodes.values():
            self.check_node(node, problems)
        for edge in graph.edges.values():
            self.check_edge(graph, edge, problems)
        touched = {name for e in graph.edges.values() for name in (e.cause, e.effect)}
        problems += [f"node '{name}': no edge touches it" for name in graph.nodes if name not in touched]
        return problems, self.loops(graph)

    def check_node(self, node: Node, problems: list[str]) -> None:
        where = f"node '{node.name}'"
        if node.passthrough and node.anomalies:
            problems.append(f"{where}: is passthrough and also has anomalies")
        if node.source_kind == "metric":
            self.check_metric_node(node, where, problems)
        else:
            self.check_record_node(node, where, problems)

    def check_metric_node(self, node: Node, where: str, problems: list[str]) -> None:
        if node.id:
            problems.append(f"{where}: a metric node has no rows, so it cannot name an id field")
        if node.source not in self.registry.metrics:
            problems.append(f"{where}: metric '{node.source}' is not in the registry")
        elif node.dimension not in self.registry.metrics[node.source] or node.dimension == "day":
            problems.append(f"{where}: metric '{node.source}' has no dimension '{node.dimension}' to split by")
        for anomaly in node.anomalies:
            if anomaly.kind not in METRIC_KINDS:
                problems.append(f"{where}: anomaly '{anomaly.kind}' needs rows, a metric node can only use {', '.join(sorted(METRIC_KINDS))}")

    def check_record_node(self, node: Node, where: str, problems: list[str]) -> None:
        record = self.registry.records.get(node.source)
        if record is None:
            problems.append(f"{where}: record type '{node.source}' is not in the registry")
            return
        listed = self.contracts.get(record.entity)
        if listed is None:
            problems.append(f"{where}: entity '{record.entity}' is in no contract under docs/sap")
        elif node.id and node.id not in listed:
            problems.append(f"{where}: id field '{node.id}' is not in {record.entity} in the contract")
        for anomaly in node.anomalies:
            if anomaly.kind not in RECORD_KINDS:
                problems.append(f"{where}: anomaly '{anomaly.kind}' needs a metric, a record node can only use {', '.join(sorted(RECORD_KINDS))}")
            for name in FIELD_PARAMS:
                value = anomaly.params.get(name)
                if value and listed is not None and value not in listed:
                    problems.append(f"{where}: anomaly '{anomaly.kind}' uses field '{value}' that {record.entity} does not have in the contract")

    def check_edge(self, graph: Graph, edge, problems: list[str]) -> None:
        where = f"edge '{edge.name}'"
        for side, field in (("cause", edge.cause_field), ("effect", edge.effect_field)):
            node = graph.nodes[getattr(edge, side)]
            self.check_join_field(node, field, where, side, problems)
        cause = graph.nodes[edge.cause]
        defined = {a.kind for a in cause.anomalies}
        if cause.passthrough and edge.carries:
            problems.append(f"{where}: carries {list(edge.carries)} but its cause '{cause.name}' is passthrough")
        for kind in edge.carries:
            if kind not in defined and not cause.passthrough:
                problems.append(f"{where}: carries '{kind}' but its cause '{cause.name}' has no such anomaly")
        effect = graph.nodes[edge.effect]
        shown = {a.kind for a in effect.anomalies}
        if effect.passthrough and edge.shows:
            problems.append(f"{where}: shows {list(edge.shows)} but its effect '{effect.name}' is passthrough")
        for kind in edge.shows:
            if kind not in shown and not effect.passthrough:
                problems.append(f"{where}: shows '{kind}' but its effect '{effect.name}' has no such anomaly")

    def check_join_field(self, node: Node, field: str, where: str, side: str, problems: list[str]) -> None:
        if node.source_kind == "metric":
            if field != "key":
                problems.append(f"{where}: the {side} side is the metric node '{node.name}', its join field must be 'key', not '{field}'")
            return
        record = self.registry.records.get(node.source)
        if record is not None and field not in record.key_fields:
            problems.append(f"{where}: join field '{field}' is not a key field of record type '{node.source}' (use one of {', '.join(record.key_fields)})")
        listed = self.contracts.get(record.entity) if record else None
        if listed is not None and field not in listed:
            problems.append(f"{where}: join field '{field}' is not in {record.entity} in the contract")

    def loops(self, graph: Graph) -> list[str]:
        following: dict[str, set[str]] = {name: set() for name in graph.nodes}
        for edge in graph.edges.values():
            following[edge.cause].add(edge.effect)
        reach = {name: self.closure(following, name) for name in graph.nodes}
        groups = {
            frozenset(m for m in graph.nodes if m in reach[name] and name in reach[m])
            for name in graph.nodes
            if name in reach[name]
        }
        return [f"info: {', '.join(sorted(group))} form a loop; walks stop at their limits" for group in sorted(groups, key=sorted)]

    def closure(self, following: dict[str, set[str]], start: str) -> set[str]:
        seen: set[str] = set()
        stack = list(following[start])
        while stack:
            current = stack.pop()
            if current not in seen:
                seen.add(current)
                stack.extend(following[current])
        return seen
