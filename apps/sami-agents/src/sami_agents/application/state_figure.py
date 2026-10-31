from datetime import date
from decimal import Decimal

from sami_agents.application.analyse_question import window_of
from sami_agents.domain.entities.figure import Figure
from sami_agents.domain.entities.question import Question
from sami_agents.domain.errors import DataUnavailable
from sami_agents.domain.gateways.data_source import DataSource


class StateFigure:
    def __init__(self, source: DataSource, significant_percent: float = 5):
        self.source = source
        self.significant_percent = Decimal(str(significant_percent))

    def execute(self, question: Question, token: str, today: date) -> Figure:
        if not any(m.name == question.metric for m in self.source.metrics(token)):
            raise DataUnavailable(f"metric '{question.metric}' is not registered")
        window = window_of(question.month)
        so_far = question.month >= today.replace(day=1)
        totals = self.source.compare(token, question.metric, window, None, 1)
        if not totals or (totals[0].current == 0 and (so_far or totals[0].previous == 0)):
            return Figure(question, window, "", Decimal(0), Decimal(0), Decimal(0), None, False, so_far)
        total = totals[0]
        return Figure(question, window, total.currency, total.current, total.previous, total.change, total.change_percent, self.significant(total), so_far)

    def significant(self, total) -> bool:
        if total.change_percent is None:
            return total.current > 0
        return abs(total.change_percent) >= self.significant_percent
