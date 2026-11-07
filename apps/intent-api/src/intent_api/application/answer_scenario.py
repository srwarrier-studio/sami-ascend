from datetime import date

from intent_api.application import wording
from intent_api.application.analysis.answer_why import AnswerWhy
from intent_api.application.comparison_window import comparison_window, previous_month
from intent_api.domain.entities.answer import Answer, AnswerRule, Block
from intent_api.domain.entities.period import Period
from intent_api.domain.gateways.metric_source import MetricSource

READ_ALL = 50
YEAR_TREND_MONTHS = 12
MONTH_TREND_MONTHS = 6


def previous_month_start(day: date) -> date:
    year, month = previous_month(day.year, day.month)
    return date(year, month, 1)


class AnswerScenario:
    def __init__(self, source: MetricSource, top: int = 5, why: AnswerWhy | None = None):
        self.source = source
        self.top = top
        self.why = why

    def execute(self, rule: AnswerRule, period: Period, token: str, company: str = "all", currency: str | None = None, today: date | None = None, direction: str = "change", base: Period | None = None, top: int | None = None) -> Answer:
        if rule.response == "why":
            return Answer(rule.scenario, tuple(self.why.execute(rule, period, token, today or date.today(), company, currency, direction)))
        scoped = AnswerScenario(self.source.for_company(None if company == "all" else company), top or self.top)
        build = {"value": scoped.value, "compare": lambda *args: scoped.compare(*args, base), "trend": scoped.trend, "ranking": scoped.ranking}[rule.response]
        return Answer(rule.scenario, tuple(build(rule, period, token)))

    def value(self, rule: AnswerRule, period: Period, token: str) -> list[Block]:
        comparisons = self.source.compare(token, rule.metric, comparison_window(period, None), None, 1)
        if not comparisons:
            return [self.text(wording.nothing_recorded(rule.metric, period))]
        return [self.text(*[wording.value_line(rule.metric, period, comparison) for comparison in comparisons])]

    def compare(self, rule: AnswerRule, period: Period, token: str, base: Period | None = None) -> list[Block]:
        window = comparison_window(period, rule.against, base)
        comparisons = self.source.compare(token, rule.metric, window, None, 1)
        if not comparisons:
            return [self.text(wording.nothing_recorded(rule.metric, period))]
        before = self.before_label(period, window, base)
        return [self.text(*[wording.compare_line(rule.metric, period, before, comparison) for comparison in comparisons])]

    def before_label(self, period: Period, window, base: Period | None = None) -> str:
        if base is not None:
            return base.label
        if period.kind == "year":
            return str(window.compare_start.year)
        if period.kind == "month":
            return window.compare_start.strftime("%B %Y")
        return f"{window.compare_start:%d %b %Y} to {window.compare_end:%d %b %Y}"

    def trend(self, rule: AnswerRule, period: Period, token: str) -> list[Block]:
        months = YEAR_TREND_MONTHS if period.kind == "year" else MONTH_TREND_MONTHS
        last = period.end.replace(day=1) if period.complete else previous_month_start(period.end)
        figures = [figure for figure in self.source.month(token, rule.metric, last, months) if figure.trend]
        if not figures:
            return [self.text(wording.nothing_recorded(rule.metric, period))]
        blocks = [self.text(*[wording.trend_line(rule.metric, figure) for figure in figures])]
        for figure in figures:
            points = [{"month": f"{point.year}-{point.month:02d}", "value": str(point.amount)} for point in figure.trend]
            blocks.append(Block("trend", {"metric": rule.metric, "currency": figure.currency, "points": points, "marked": []}))
        return blocks

    def ranking(self, rule: AnswerRule, period: Period, token: str) -> list[Block]:
        comparisons = [
            comparison
            for comparison in self.source.compare(token, rule.metric, comparison_window(period, None), rule.by, READ_ALL)
            if any(row.current > 0 for row in comparison.rows)
        ]
        if not comparisons:
            return [self.text(wording.nothing_recorded(rule.metric, period))]
        ranked = [(comparison, sorted((row for row in comparison.rows if row.current > 0), key=lambda row: (-row.current, row.key))[: self.top]) for comparison in comparisons]
        lines = [wording.ranking_line(rule.metric, rule.by, period, comparison, rows[0]) for comparison, rows in ranked]
        if any(comparison.truncated for comparison, _ in ranked):
            lines.append(wording.truncated_line(rule.by, READ_ALL))
        blocks = [self.text(*lines)]
        for comparison, rows in ranked:
            title = wording.ranking_title(rule.by, period, comparison.currency, len(ranked) > 1)
            blocks.append(Block("table", {"title": title, "columns": ["Name", "Current"], "rows": [{"name": row.name, "current": str(row.current)} for row in rows]}))
        return blocks

    def text(self, *lines: str) -> Block:
        return Block("text", {"lines": list(lines)})
