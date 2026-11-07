from dataclasses import replace
from datetime import date

from intent_api.application.answer_scenario import AnswerScenario
from intent_api.application.match_question import MatchQuestion
from intent_api.application.read_currency import read_currency
from intent_api.application.read_direction import read_direction
from intent_api.application.read_period import ReadPeriod
from intent_api.domain.entities.answer import AnswerRule
from intent_api.domain.entities.match import NOT_ANSWERABLE_YET, PERIOD_NOT_SUPPORTED
from intent_api.domain.entities.reply import Reply
from intent_api.domain.errors import PeriodNotSupported
from intent_api.domain.gateways.unanswered_log import UnansweredLog


MAX_PERIODS = 6


class AnswerQuestion:
    def __init__(self, matcher: MatchQuestion, rules: dict[str, AnswerRule], scenarios: AnswerScenario, periods: ReadPeriod, log: UnansweredLog | None = None):
        self.matcher = matcher
        self.rules = rules
        self.scenarios = scenarios
        self.periods = periods
        self.log = log

    def execute(self, question: str, token: str, today: date, company: str = "all") -> Reply:
        match = self.matcher.match(question)
        if not match.answered:
            return self.refused(question, Reply(match, reason=match.reason))
        answers = []
        for selected in match.selected:
            rule = self.rules.get(selected.scenario)
            if rule is None:
                continue
            try:
                answers += self.answer_periods(question, rule, token, company, today)
            except PeriodNotSupported as error:
                return self.refused(question, Reply(match, reason=PERIOD_NOT_SUPPORTED, periods=tuple(error.periods)))
        if not answers:
            return self.refused(question, Reply(match, reason=NOT_ANSWERABLE_YET))
        return Reply(match, tuple(answers))

    def answer_periods(self, question: str, rule: AnswerRule, token: str, company: str, today: date) -> list:
        currency, direction = read_currency(question), read_direction(question)
        base = None
        try:
            periods = [self.periods.execute(question, today, rule.against)]
        except PeriodNotSupported as error:
            if error.reason != "more than one period":
                raise
            periods = self.periods.each(question, today, rule.against)
            pair = self.periods.pair(question, today, rule.against) if rule.response == "compare" else None
            if pair:
                periods, base = [pair[0]], pair[1]
            elif len(periods) > MAX_PERIODS:
                raise PeriodNotSupported([period.label for period in periods], f"more than {MAX_PERIODS} periods")
        return [self.scenarios.execute(rule, period, token, company, currency, today, direction, base) for period in periods]

    def refused(self, question: str, reply: Reply) -> Reply:
        if self.log:
            self.log.record(question, replace(reply.match, reason=reply.reason))
        return reply
