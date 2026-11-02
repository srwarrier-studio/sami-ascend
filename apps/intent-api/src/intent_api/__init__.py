import sys


def main() -> None:
    if sys.argv[1:2] == ["domain"]:
        from intent_api.entrypoint.domain import main as domain

        domain(sys.argv[2:])
        return
    if sys.argv[1:2] == ["scenarios"]:
        from intent_api.entrypoint.scenarios import main as scenarios

        scenarios(sys.argv[2:])
        return
    if sys.argv[1:2] == ["answers"]:
        from intent_api.entrypoint.answers import main as answers

        answers(sys.argv[2:])
        return
    if sys.argv[1:2] == ["eval"]:
        from intent_api.entrypoint.evaluate import main as evaluate

        evaluate(sys.argv[2:])
        return
    if sys.argv[1:2] == ["training"]:
        from intent_api.entrypoint.training import main as training

        training(sys.argv[2:])
        return
    if sys.argv[1:2] == ["why-eval"]:
        from intent_api.entrypoint.why_eval import main as why_eval

        why_eval(sys.argv[2:])
        return
    if sys.argv[1:2] == ["graph"]:
        from intent_api.entrypoint.graph import main as graph

        graph(sys.argv[2:])
        return
    if sys.argv[1:2] == ["unanswered"]:
        from intent_api.entrypoint.unanswered import main as unanswered

        unanswered()
        return
    from intent_api.entrypoint.run import main as run

    run()
