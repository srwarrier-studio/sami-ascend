from intent_api.application.analysis.analyse_question import Thresholds
from intent_api.application.analysis.answer_why import AnswerWhy
from intent_api.application.answer_question import AnswerQuestion
from intent_api.application.answer_scenario import AnswerScenario
from intent_api.application.match_question import MatchQuestion
from intent_api.application.read_period import ReadPeriod
from intent_api.application.read_qualifiers import ReadQualifiers
from intent_api.domain.analysis.data_source import DataSource
from intent_api.domain.gateways.metric_source import MetricSource
from intent_api.infrastructure.answers_loader import load_answers
from intent_api.infrastructure.dateparser_periods import DateparserPeriods
from intent_api.infrastructure.period_words_loader import load_period_words
from intent_api.infrastructure.qualifier_words_loader import load_qualifier_words
from intent_api.infrastructure.graph_loader import load_graph
from intent_api.infrastructure.jsonl_unanswered_log import JsonlUnansweredLog
from intent_api.infrastructure.library_loader import load_library
from intent_api.infrastructure.settings import GRAPH_FILE, Settings
from intent_api.infrastructure.synapse_data_source import SynapseDataSource
from intent_api.infrastructure.synapse_metric_source import SynapseMetricSource


def build_answerer(settings: Settings, matcher: MatchQuestion, source: MetricSource | None = None, analysis: DataSource | None = None) -> AnswerQuestion:
    rules = load_answers(load_library())
    thresholds = Thresholds(settings.significant_percent, settings.mover_min_percent, settings.mover_min_share, settings.price_majority_percent)
    why = AnswerWhy(analysis or SynapseDataSource(settings), load_graph(GRAPH_FILE), thresholds)
    scenarios = AnswerScenario(source or SynapseMetricSource(settings), settings.top_ranked, why)
    return AnswerQuestion(matcher, rules, scenarios, ReadPeriod(load_period_words(), DateparserPeriods()), ReadQualifiers(load_qualifier_words()), JsonlUnansweredLog(settings.unanswered_log))
