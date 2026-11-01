import argparse
import time

from intent_api.application.choose_scenarios import ChooseScenarios
from intent_api.application.evaluate_matches import EvaluateMatches, describe, describe_failures, sweep_table
from intent_api.application.match_question import MatchQuestion
from intent_api.application.read_domain import ReadDomain
from intent_api.domain.errors import ClassifierUnavailable
from intent_api.infrastructure.caching_classifier import CachingClassifier
from intent_api.infrastructure.eval_loader import load_cases
from intent_api.infrastructure.laya_choice_classifier import LayaChoiceClassifier
from intent_api.infrastructure.library_loader import load_library
from intent_api.infrastructure.settings import Settings

DOMAIN_GRID = [0.0, 0.4, 0.5, 0.6, 0.7]
SCENARIO_GRID = [0.0, 0.3, 0.4, 0.5, 0.6]


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="intent-api eval")
    parser.add_argument("--final", action="store_true", help="also run the held-out questions, with the chosen thresholds only")
    parser.add_argument("--show", action="store_true", help="list every question that was not exactly right")
    parser.add_argument("--domain-min", type=float, help="chosen domain threshold (default: the setting)")
    parser.add_argument("--scenario-min", type=float, help="chosen scenario threshold (default: the setting)")
    args = parser.parse_args(argv)
    settings = Settings()
    library = load_library()
    classifier = CachingClassifier(LayaChoiceClassifier(settings))

    def build(domain_min: float, scenario_min: float) -> MatchQuestion:
        return MatchQuestion(ReadDomain(classifier, library.domains), ChooseScenarios(classifier, library, settings.max_scenarios, scenario_min), library, domain_min)

    cases = load_cases(library)
    tune = [case for case in cases if not case.heldout]
    evaluate = EvaluateMatches(build)
    domain_min = settings.domain_min_probability if args.domain_min is None else args.domain_min
    scenario_min = settings.scenario_min_probability if args.scenario_min is None else args.scenario_min
    try:
        started = time.time()
        chosen = evaluate.execute(tune, domain_min, scenario_min)
        seconds = time.time() - started
        print(f"tuning questions ({len(tune)}), model {settings.laya_model}, {seconds / len(tune):.2f} s per question")
        print(describe(chosen))
        if args.show:
            print(describe_failures(chosen))
        print("\nthreshold sweep (tuning questions only)")
        print(sweep_table(evaluate.sweep(tune, DOMAIN_GRID, SCENARIO_GRID)))
        if args.final:
            held = [case for case in cases if case.heldout]
            final = evaluate.execute(held, domain_min, scenario_min)
            print(f"\nheld-out questions ({len(held)}), thresholds not tuned on them")
            print(describe(final))
            if args.show:
                print(describe_failures(final))
    except ClassifierUnavailable as error:
        raise SystemExit(f"cannot_classify_now ({error}): start Laya first, see the README")
