import argparse

from intent_api.application.describe_library import DescribeLibrary
from intent_api.domain.errors import LibraryError
from intent_api.infrastructure.library_loader import load_library


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="intent-api scenarios")
    parser.add_argument("command", choices=["check", "show"])
    args = parser.parse_args(argv)
    try:
        describe = DescribeLibrary(load_library())
    except LibraryError as error:
        raise SystemExit("\n".join(error.problems))
    print(describe.summary() if args.command == "check" else describe.show())
