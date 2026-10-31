import argparse
import sys
from pathlib import Path

from sami_agents.application.check_graph import CheckGraph
from sami_agents.application.show_graph import show_mermaid, show_text
from sami_agents.domain.errors import GraphError
from sami_agents.infrastructure.graph_loader import load_graph
from sami_agents.infrastructure.registry_info_loader import load_contract_fields, load_registry_info
from sami_agents.infrastructure.settings import CONTRACTS_FOLDER, GRAPH_FILE, REGISTRY_FILE


def run_check(graph_path: Path, registry_path: Path, contracts_path: Path) -> int:
    try:
        graph = load_graph(graph_path)
    except GraphError as error:
        print("\n".join(error.problems))
        return 1
    problems, info = CheckGraph(load_registry_info(registry_path), load_contract_fields(contracts_path)).execute(graph)
    print("\n".join([*problems, *info, *([] if problems else ["ok"])]))
    return 1 if problems else 0


def run_show(graph_path: Path, mermaid: bool) -> int:
    try:
        graph = load_graph(graph_path)
    except GraphError as error:
        print("\n".join(error.problems))
        return 1
    print(show_mermaid(graph) if mermaid else show_text(graph))
    return 0


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="sami-agents graph")
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("check", "show"):
        command = commands.add_parser(name)
        command.add_argument("--graph", type=Path, default=GRAPH_FILE)
        if name == "check":
            command.add_argument("--registry", type=Path, default=REGISTRY_FILE)
            command.add_argument("--contracts", type=Path, default=CONTRACTS_FOLDER)
        else:
            command.add_argument("--mermaid", action="store_true")
    args = parser.parse_args(argv)
    code = run_check(args.graph, args.registry, args.contracts) if args.command == "check" else run_show(args.graph, args.mermaid)
    sys.exit(code)
