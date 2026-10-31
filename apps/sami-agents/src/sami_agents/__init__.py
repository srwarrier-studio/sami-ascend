import sys


def main() -> None:
    if sys.argv[1:2] == ["eval"]:
        from sami_agents.entrypoint.evaluate import main as evaluate

        evaluate(sys.argv[2:])
        return
    if sys.argv[1:2] == ["graph"]:
        from sami_agents.entrypoint.graph import main as graph

        graph(sys.argv[2:])
        return
    from sami_agents.entrypoint.run import main as run

    run()
