from datetime import date

from sami_agents.application import wording
from sami_agents.application.analyse_question import AnalyseQuestion
from sami_agents.application.analysis_json import analysis_json, row_json, step_json
from sami_agents.application.model_checks import accept_question, accept_rewrite
from sami_agents.application.question_reader import HELP, NOT_FINISHED, QuestionReader
from sami_agents.domain.entities.analysis import Analysis
from sami_agents.domain.entities.question import Question
from sami_agents.domain.errors import DataUnavailable
from sami_agents.domain.gateways.data_source import DataSource
from sami_agents.domain.gateways.question_model import HeadlineRewriter, QuestionModel

TREND_MONTHS = 6
MOCK_LABEL = "Mock data (butterfly)"
TABLE_COLUMNS = ["Name", "Current", "Previous", "Change", "Share of change", "Volume effect", "Price effect"]


def previous_month_of(month: date) -> date:
    return date(month.year - 1, 12, 1) if month.month == 1 else date(month.year, month.month - 1, 1)


class AnswerQuestion:
    def __init__(
        self,
        reader: QuestionReader,
        analyser: AnalyseQuestion,
        source: DataSource,
        metrics: list[str],
        mock: bool = True,
        model: QuestionModel | None = None,
        rewriter: HeadlineRewriter | None = None,
    ):
        self.reader = reader
        self.analyser = analyser
        self.source = source
        self.metrics = metrics
        self.mock = mock
        self.model = model
        self.rewriter = rewriter

    def execute(self, text: str, token: str, today: date) -> dict:
        read = self.reader.read(text, today)
        question = read.question
        if question is None and read.problem == "unreadable" and self.model is not None:
            question = accept_question(self.model.read(text, self.metrics), self.metrics, today)
        if question is None:
            return self.refusal(NOT_FINISHED if read.problem == "not_finished" else HELP)
        analysis = self.analyser.execute(question, token, today)
        trend = self.trend_block(question, token, analysis)
        lines = wording.lines(analysis)
        if self.rewriter is not None:
            lines[0] = accept_rewrite(self.rewriter.rewrite(lines[0]), lines[0]) or lines[0]
        blocks = [{"type": "text", "lines": lines}, *trend, *self.table_blocks(analysis), *self.evidence_blocks(analysis)]
        return {
            "readable": True,
            "question": {"metric": question.metric, "direction": question.direction, "month": question.month.strftime("%Y-%m"), "compared_with": previous_month_of(question.month).strftime("%Y-%m")},
            "label": MOCK_LABEL if self.mock else None,
            "blocks": blocks,
            "analysis": analysis_json(analysis),
        }

    def refusal(self, message: str) -> dict:
        return {"readable": False, "question": None, "label": None, "blocks": [{"type": "text", "lines": [message]}], "analysis": None}

    def trend_block(self, question: Question, token: str, analysis: Analysis) -> list[dict]:
        if not analysis.currency:
            return []
        try:
            points = self.source.trend(token, question.metric, question.month, TREND_MONTHS)
        except DataUnavailable:
            analysis.limits.append("The trend of the last months could not be loaded.")
            return []
        marked = [previous_month_of(question.month).strftime("%Y-%m"), question.month.strftime("%Y-%m")]
        return [{"type": "trend", "metric": question.metric, "currency": analysis.currency, "points": [{"month": p.month, "value": str(p.amount)} for p in points], "marked": marked}]

    def table_blocks(self, analysis: Analysis) -> list[dict]:
        return [
            {"type": "table", "title": f"By {dimension}", "columns": TABLE_COLUMNS, "rows": [row_json(row) for row in rows]}
            for dimension, rows in analysis.tables.items() if rows
        ]

    def evidence_blocks(self, analysis: Analysis) -> list[dict]:
        blocks = []
        for finding in analysis.findings:
            offset = 0
            for path in finding.paths:
                steps = []
                for i, step in enumerate(path):
                    steps.append({**step_json(step), "summary": wording.step_sentence(step, finding.causes[offset + i].key)})
                offset += len(path)
                blocks.append({"type": "evidence", "finding": finding.name, "steps": steps})
        return blocks
