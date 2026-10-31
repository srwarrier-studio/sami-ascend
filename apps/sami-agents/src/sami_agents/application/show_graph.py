import re

from sami_agents.domain.entities.graph import Graph


def node_line(node) -> str:
    source = f"{node.source_kind}:{node.source}" + (f".{node.dimension}" if node.dimension else "")
    if node.passthrough:
        tests = "passthrough"
    elif node.anomalies:
        tests = ", ".join(a.kind for a in node.anomalies)
    else:
        tests = "no anomaly"
    return f"  {node.name:<18} {source:<32} {tests}"


def edge_line(edge) -> str:
    join = f"{edge.cause}.{edge.cause_field} = {edge.effect}.{edge.effect_field}"
    carries = ", ".join(edge.carries) or "-"
    shows = ", ".join(edge.shows) or "-"
    return f"  {edge.name:<26} {edge.cause} -> {edge.effect}   join {join}   carries {carries}   shows {shows}   lookback {edge.lookback_days}d"


def show_text(graph: Graph) -> str:
    lines = ["Nodes", *(node_line(n) for n in graph.nodes.values()), "", "Edges (cause -> effect)", *(edge_line(e) for e in graph.edges.values())]
    return "\n".join(lines)


def mermaid_id(name: str) -> str:
    return re.sub(r"\W", "_", name)


def show_mermaid(graph: Graph) -> str:
    lines = ["graph LR"]
    for node in graph.nodes.values():
        shape = f'{mermaid_id(node.name)}(["{node.name}"])' if node.source_kind == "metric" else f'{mermaid_id(node.name)}["{node.name}"]'
        lines.append(f"  {shape}")
    for edge in graph.edges.values():
        label = ", ".join(edge.carries) or "link"
        lines.append(f'  {mermaid_id(edge.cause)} -->|"{label}"| {mermaid_id(edge.effect)}')
    return "\n".join(lines)
