from intent_api.application.answer_question import AnswerQuestion
from intent_api.application.answer_scenario import AnswerScenario
from intent_api.application.match_question import MatchQuestion
from intent_api.application.read_period import ReadPeriod
from intent_api.domain.gateways.metric_source import MetricSource
from intent_api.infrastructure.answers_loader import load_answers
from intent_api.infrastructure.jsonl_unanswered_log import JsonlUnansweredLog
from intent_api.infrastructure.library_loader import load_library
from intent_api.infrastructure.settings import Settings
from intent_api.infrastructure.synapse_metric_source import SynapseMetricSource


def build_answerer(settings: Settings, matcher: MatchQuestion, source: MetricSource | None = None) -> AnswerQuestion:
    rules = load_answers(load_library())
    scenarios = AnswerScenario(source or SynapseMetricSource(settings), settings.top_ranked)
    return AnswerQuestion(matcher, rules, scenarios, ReadPeriod(), JsonlUnansweredLog(settings.unanswered_log))
