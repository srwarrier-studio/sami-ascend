from sami_agents.application.analyse_question import AnalyseQuestion, Thresholds
from sami_agents.application.answer_question import AnswerQuestion
from sami_agents.application.case_reader import CaseReader
from sami_agents.application.question_reader import QuestionReader
from sami_agents.infrastructure.graph_loader import load_graph
from sami_agents.infrastructure.laya_case_model import LayaCaseModel
from sami_agents.infrastructure.ollama_question_model import OllamaHeadlineRewriter, OllamaQuestionModel
from sami_agents.infrastructure.settings import GRAPH_FILE, Settings
from sami_agents.infrastructure.synapse_data_source import SynapseDataSource
from sami_agents.infrastructure.understanding_loader import load_understanding


def build_analyst(settings: Settings, source: SynapseDataSource | None = None) -> AnswerQuestion:
    source = source or SynapseDataSource(settings)
    understanding = load_understanding()
    thresholds = Thresholds(settings.significant_percent, settings.mover_min_percent, settings.mover_min_share, settings.price_majority_percent)
    use_model = bool(settings.ollama_model)
    rules = QuestionReader(understanding)
    reader = CaseReader(rules, LayaCaseModel(settings), settings.pass_min_confidence) if settings.laya_url else rules
    return AnswerQuestion(
        reader,
        AnalyseQuestion(source, load_graph(GRAPH_FILE), thresholds),
        source,
        list(understanding.metrics),
        settings.sap_is_mock,
        OllamaQuestionModel(settings) if use_model else None,
        OllamaHeadlineRewriter(settings) if use_model else None,
    )
