from dataclasses import replace
from datetime import date

from intent_api.application import wording
from intent_api.application.answer_scenario import AnswerScenario
from intent_api.application.match_question import MatchQuestion
from intent_api.application.read_currency import read_currency
from intent_api.application.read_direction import read_direction
from intent_api.application.read_period import ReadPeriod
from intent_api.application.read_qualifiers import MAX_TOP, ReadQualifiers
from intent_api.domain.entities.answer import Answer, AnswerRule, Block
from intent_api.domain.entities.match import NOT_ANSWERABLE_YET, PERIOD_NOT_SUPPORTED
from intent_api.domain.entities.reply import Reply
from intent_api.domain.errors import PeriodNotSupported
from intent_api.domain.gateways.unanswered_log import UnansweredLog


MAX_PERIODS = 6


class AnswerQuestion:
    def __init__(self, matcher: MatchQuestion, rules: dict[str, AnswerRule], scenarios: AnswerScenario, periods: ReadPeriod, qualifiers: ReadQualifiers, log: UnansweredLog | None = None):
        self.matcher = matcher
        self.rules = rules
        self.scenarios = scenarios
        self.periods = periods
        self.qualifiers = qualifiers
        self.log = log

    def execute(self, question: str, token: str, today: date, company: str = "all") -> Reply:
        match = self.matcher.match(question)
        if not match.answered:
            return self.refused(question, Reply(match, reason=match.reason))
        qualifiers = self.qualifiers.read(question)
        if qualifiers.refused:
            message = wording.qualifier_refusal(qualifiers.names, qualifiers.quantities, qualifiers.currencies)
            return self.refused(question, Reply(match, reason=NOT_ANSWERABLE_YET, message=message))
        answers = []
        used: list = []
        for selected in match.selected:
            rule = self.rules.get(selected.scenario)
            if rule is None:
                continue
            try:
                periods, built = self.answer_periods(question, rule, token, company, today, qualifiers)
            except PeriodNotSupported as error:
                message = wording.period_refusal(error.reason, error.periods)
                return self.refused(question, Reply(match, reason=PERIOD_NOT_SUPPORTED, periods=tuple(error.periods), message=message))
            answers += built
            used += [period for period in periods if period not in used]
        if not answers:
            return self.refused(question, Reply(match, reason=NOT_ANSWERABLE_YET))
        return Reply(match, tuple(answers), read=tuple(used))

    def answer_periods(self, question: str, rule: AnswerRule, token: str, company: str, today: date, qualifiers) -> tuple[list, list[Answer]]:
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
        answers = [self.noted(self.scenarios.execute(rule, period, token, company, currency, today, direction, base, qualifiers.top), period, qualifiers if rule.response == "ranking" else None) for period in periods]
        return periods, answers

    def noted(self, answer: Answer, period, qualifiers=None) -> Answer:
        lines = [period.note] if period.note else []
        if qualifiers is not None and qualifiers.top_asked and qualifiers.top_asked > MAX_TOP:
            lines.append(wording.top_limit_line(qualifiers.top_asked, MAX_TOP))
        if not lines:
            return answer
        return Answer(answer.scenario, (Block("text", {"lines": lines}), *answer.blocks))

    def refused(self, question: str, reply: Reply) -> Reply:
        if self.log:
            self.log.record(question, replace(reply.match, reason=reply.reason))
        return reply
