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
    if sys.argv[1:2] == ["eval"]:
        from intent_api.entrypoint.evaluate import main as evaluate

        evaluate(sys.argv[2:])
        return
    if sys.argv[1:2] == ["unanswered"]:
        from intent_api.entrypoint.unanswered import main as unanswered

        unanswered()
        return
    from intent_api.entrypoint.run import main as run

    run()
