from datetime import date

from intent_api.domain.entities.decision import Decision
from intent_api.domain.entities.figures import Comparison, MonthFigure, Window
from intent_api.domain.entities.match import Match
from intent_api.domain.errors import ClassifierUnavailable, MetricsUnavailable
from intent_api.domain.gateways.choice_classifier import ChoiceClassifier
from intent_api.domain.gateways.metric_source import MetricSource
from intent_api.domain.gateways.unanswered_log import UnansweredLog


class FakeClassifier(ChoiceClassifier):
    def __init__(self, decision: Decision | None = None, by_text: dict[str, Decision] | None = None):
        self.decision = decision
        self.by_text = by_text or {}
        self.calls = []

    def choose(self, text: str, instructions: str, choices: dict[str, str]) -> Decision:
        self.calls.append((text, instructions, choices))
        if text in self.by_text:
            return self.by_text[text]
        if self.decision is None:
            raise ClassifierUnavailable("down")
        return self.decision


class FakeUnansweredLog(UnansweredLog):
    def __init__(self):
        self.logged = []

    def record(self, question: str, match: Match) -> None:
        self.logged.append((question, match))

    def entries(self) -> list[dict]:
        return [{"question": question, "reason": match.reason, "domain": match.domain, "did_you_mean": list(match.did_you_mean)} for question, match in self.logged]


class FakeMetricSource(MetricSource):
    def __init__(self, months: list[MonthFigure] | None = None, comparisons: list[Comparison] | None = None):
        self.months = months or []
        self.comparisons = comparisons or []
        self.down = False
        self.calls = []
        self.companies = []

    def for_company(self, company):
        self.companies.append(company)
        return self

    def month(self, token: str, metric: str, month: date, trend: int) -> list[MonthFigure]:
        self.calls.append(("month", token, metric, month, trend))
        self.check()
        return self.months

    def compare(self, token: str, metric: str, window: Window, by: str | None, top: int) -> list[Comparison]:
        self.calls.append(("compare", token, metric, window, by, top))
        self.check()
        return self.comparisons

    def check(self) -> None:
        if self.down:
            raise MetricsUnavailable("down")


def period_reader():
    from intent_api.application.read_period import ReadPeriod
    from intent_api.infrastructure.period_words_loader import load_period_words

    return ReadPeriod(load_period_words())
