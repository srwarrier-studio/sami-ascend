from intent_api.application.choose_scenarios import ChooseScenarios
from intent_api.application.match_question import MatchQuestion
from intent_api.application.read_domain import ReadDomain
from intent_api.infrastructure.jsonl_unanswered_log import JsonlUnansweredLog
from intent_api.infrastructure.laya_choice_classifier import LayaChoiceClassifier
from intent_api.infrastructure.library_loader import load_library
from intent_api.infrastructure.settings import Settings


def build_matcher(settings: Settings) -> MatchQuestion:
    library = load_library()
    classifier = LayaChoiceClassifier(settings)
    return MatchQuestion(
        ReadDomain(classifier, library.domains),
        ChooseScenarios(classifier, library, settings.max_scenarios, settings.scenario_min_probability),
        library,
        settings.domain_min_probability,
        JsonlUnansweredLog(settings.unanswered_log),
    )
