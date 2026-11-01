from dataclasses import replace
from datetime import date

from intent_api.application.answer_scenario import AnswerScenario
from intent_api.application.match_question import MatchQuestion
from intent_api.application.read_period import ReadPeriod
from intent_api.domain.entities.answer import AnswerRule
from intent_api.domain.entities.match import NOT_ANSWERABLE_YET, PERIOD_NOT_SUPPORTED
from intent_api.domain.entities.reply import Reply
from intent_api.domain.errors import PeriodNotSupported
from intent_api.domain.gateways.unanswered_log import UnansweredLog


class AnswerQuestion:
    def __init__(self, matcher: MatchQuestion, rules: dict[str, AnswerRule], scenarios: AnswerScenario, periods: ReadPeriod, log: UnansweredLog | None = None):
        self.matcher = matcher
        self.rules = rules
        self.scenarios = scenarios
        self.periods = periods
        self.log = log

    def execute(self, question: str, token: str, today: date) -> Reply:
        match = self.matcher.match(question)
        if not match.answered:
            return self.refused(question, Reply(match, reason=match.reason))
        answers = []
        for selected in match.selected:
            rule = self.rules.get(selected.scenario)
            if rule is None:
                continue
            try:
                period = self.periods.execute(question, today, rule.against)
            except PeriodNotSupported as error:
                return self.refused(question, Reply(match, reason=PERIOD_NOT_SUPPORTED, periods=tuple(error.periods)))
            answers.append(self.scenarios.execute(rule, period, token))
        if not answers:
            return self.refused(question, Reply(match, reason=NOT_ANSWERABLE_YET))
        return Reply(match, tuple(answers))

    def refused(self, question: str, reply: Reply) -> Reply:
        if self.log:
            self.log.record(question, replace(reply.match, reason=reply.reason))
        return reply
