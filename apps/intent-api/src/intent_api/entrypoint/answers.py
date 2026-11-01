import argparse

from intent_api.application.describe_answers import DescribeAnswers
from intent_api.domain.errors import LibraryError
from intent_api.infrastructure.answers_loader import load_answers
from intent_api.infrastructure.library_loader import load_library


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="intent-api answers")
    parser.add_argument("command", choices=["check"])
    parser.parse_args(argv)
    try:
        describe = DescribeAnswers(load_answers(load_library()))
    except LibraryError as error:
        raise SystemExit("\n".join(error.problems))
    print(describe.summary())
