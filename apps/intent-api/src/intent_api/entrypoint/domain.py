import argparse

from intent_api.application.read_domain import OTHER, ReadDomain
from intent_api.domain.errors import ClassifierUnavailable
from intent_api.infrastructure.domain_loader import load_domains
from intent_api.infrastructure.laya_choice_classifier import LayaChoiceClassifier
from intent_api.infrastructure.settings import Settings


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="intent-api domain")
    parser.add_argument("question")
    args = parser.parse_args(argv)
    read = ReadDomain(LayaChoiceClassifier(Settings()), load_domains())
    try:
        decision = read.execute(args.question)
    except ClassifierUnavailable as error:
        raise SystemExit(f"cannot_classify_now ({error})")
    print(f"{'refused (Other)' if decision.choice == OTHER else decision.choice}  probability {decision.probability:.2f}")
