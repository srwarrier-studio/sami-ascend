import sys


def main() -> None:
    if sys.argv[1:2] == ["eval"]:
        from sami_agents.entrypoint.evaluate import main as evaluate

        evaluate(sys.argv[2:])
        return
    if sys.argv[1:2] == ["analyst-eval"]:
        from sami_agents.entrypoint.analyst_eval import main as analyst_eval

        analyst_eval(sys.argv[2:])
        return
    if sys.argv[1:2] == ["case-eval"]:
        from sami_agents.entrypoint.case_eval import main as case_eval

        case_eval(sys.argv[2:])
        return
    if sys.argv[1:2] == ["graph"]:
        from sami_agents.entrypoint.graph import main as graph

        graph(sys.argv[2:])
        return
    from sami_agents.entrypoint.run import main as run

    run()
