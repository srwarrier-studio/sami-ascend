import re
from datetime import date

from sami_agents.domain.entities.question import Question, ReadResult
from sami_agents.infrastructure.understanding_loader import Understanding

HELP = "Ask why a metric rose or fell in a month, for example: why did sales fall in August?"
NOT_FINISHED = "That month is not over yet. Ask about a month that has finished."
MONTHS = {
    "january": 1, "jan": 1, "february": 2, "feb": 2, "march": 3, "mar": 3, "april": 4, "apr": 4, "may": 5, "june": 6, "jun": 6,
    "july": 7, "jul": 7, "august": 8, "aug": 8, "september": 9, "sep": 9, "sept": 9, "october": 10, "oct": 10,
    "november": 11, "nov": 11, "december": 12, "dec": 12,
}
MONTH_PATTERN = re.compile(r"\b(" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\b(?:\s+(\d{4}))?")


def first_position(text: str, phrases: list[str]) -> int | None:
    found = [m.start() for p in phrases if (m := re.search(rf"(?<![\w']){re.escape(p)}(?![\w'])", text))]
    return min(found) if found else None


def previous_month(day: date) -> date:
    return date(day.year - 1, 12, 1) if day.month == 1 else date(day.year, day.month - 1, 1)


class QuestionReader:
    def __init__(self, understanding: Understanding):
        self.words = understanding

    def read(self, text: str, today: date) -> ReadResult:
        lowered = " ".join(text.lower().split())
        if first_position(lowered, self.words.why) is None:
            return ReadResult(None, "unreadable")
        metric = self.metric(lowered)
        month = self.month(lowered, today)
        if metric is None or month is None:
            return ReadResult(None, "unreadable")
        if month >= today.replace(day=1):
            return ReadResult(None, "not_finished")
        return ReadResult(Question(metric, self.direction(lowered), month))

    def metric(self, text: str) -> str | None:
        found = {name: pos for name, words in self.words.metrics.items() if (pos := first_position(text, words)) is not None}
        return min(found, key=lambda name: (found[name], name)) if found else None

    def direction(self, text: str) -> str:
        found = {name: pos for name in ("rise", "fall", "change") if (pos := first_position(text, getattr(self.words, name))) is not None}
        return min(found, key=found.get) if found else "change"

    def month(self, text: str, today: date) -> date | None:
        if re.search(r"\b(last|previous) month\b", text):
            return previous_month(today.replace(day=1))
        if re.search(r"\b(this|current) month\b", text):
            return today.replace(day=1)
        match = MONTH_PATTERN.search(text)
        if match is None:
            return None
        number = MONTHS[match.group(1)]
        if match.group(2):
            return date(int(match.group(2)), number, 1)
        year = today.year if number <= today.month else today.year - 1
        return date(year, number, 1)
