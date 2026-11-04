from datetime import date

from intent_api.application.analysis import analysis_blocks, why_wording
from intent_api.application.analysis.analyse_question import AnalyseQuestion, Thresholds
from intent_api.domain.analysis.data_source import DataSource
from intent_api.domain.analysis.question import Question
from intent_api.domain.entities.answer import AnswerRule, Block
from intent_api.domain.entities.graph import Graph
from intent_api.domain.entities.period import Period
from intent_api.domain.errors import DataUnavailable, MetricsUnavailable

TREND_MONTHS = 6
NEEDS_A_FINISHED_MONTH = "A why-question needs one finished month, for example August 2026."


class AnswerWhy:
    def __init__(self, source: DataSource, graph: Graph, thresholds: Thresholds = Thresholds()):
        self.source = source
        self.graph = graph
        self.thresholds = thresholds

    def execute(self, rule: AnswerRule, period: Period, token: str, today: date, company: str, currency: str | None, direction: str = "change") -> list[Block]:
        if period.kind != "month" or not period.complete:
            return [Block("text", {"lines": [NEEDS_A_FINISHED_MONTH]})]
        scoped = self.source.for_company(None if company == "all" else company)
        question = Question(rule.metric, direction, period.start, currency=currency)
        try:
            analysis = AnalyseQuestion(scoped, self.graph, self.thresholds).execute(question, token, today)
            trend = scoped.trend(token, rule.metric, period.start, TREND_MONTHS) if analysis.currency else []
        except DataUnavailable as error:
            raise MetricsUnavailable(str(error)) from error
        blocks = [Block("findings", analysis_blocks.findings_block(analysis, company))] if analysis.currency else [Block("text", {"lines": why_wording.lines(analysis, company)})]
        if trend:
            blocks.append(Block("trend", analysis_blocks.trend_block(analysis, trend)))
        blocks += [Block("table", data) for data in analysis_blocks.table_blocks(analysis)]
        blocks += [Block("evidence", data) for data in analysis_blocks.evidence_blocks(analysis)]
        return blocks
