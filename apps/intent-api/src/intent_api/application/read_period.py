import calendar
import difflib
import re
from dataclasses import dataclass, replace
from datetime import date, timedelta

from intent_api.domain.entities.period import Period
from intent_api.domain.errors import PeriodNotSupported
from intent_api.domain.gateways.fallback_periods import FallbackPeriods

MONTHS = {name.lower(): number for number, name in enumerate(calendar.month_name) if name}
MONTHS.update({name.lower(): number for number, name in enumerate(calendar.month_abbr) if name})
MONTHS["sept"] = 9
MONTH_NAMES = "|".join(sorted(MONTHS, key=len, reverse=True))
NUMBER_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10, "eleven": 11, "twelve": 12}
ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4}
UNIT_DAYS = {"day": 1, "week": 7}
YEAR = r"(?:19|20)\d\d"

DATE = re.compile(r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b")
FUZZY_MIN_LENGTH = 5
FUZZY_CUTOFF = 0.88
BASE_VOCABULARY = ("quarter", "half", "month", "since", "first", "second", "third", "fourth")


def alternatives(items: list[str]) -> str:
    return "|".join(r"\s+".join(map(re.escape, item.split())) for item in sorted(items, key=len, reverse=True))


@dataclass(frozen=True)
class Mention:
    period: Period
    bare: str | None


class ReadPeriod:
    def __init__(self, words: dict[str, list[str]], fallback: FallbackPeriods | None = None):
        self.fallback = fallback
        self.patterns = self.build_patterns(words)
        self.unreadable = self.patterns["UNREAD_WORDS"]
        singles = {word for group in words.values() for word in group if " " not in word and len(word) >= FUZZY_MIN_LENGTH}
        self.vocabulary = sorted(singles | set(BASE_VOCABULARY) | {name for name in MONTHS if len(name) >= FUZZY_MIN_LENGTH})

    def build_patterns(self, words: dict[str, list[str]]) -> dict[str, re.Pattern]:
        last, this = alternatives(words["last"]), alternatives(words["this"])
        to, between, and_ = alternatives(words["range_to"]), alternatives(words["between"]), alternatives(words["and"])
        fy = alternatives(words["financial_year"])
        month = rf"(?:{MONTH_NAMES})(?:\s+{YEAR})?"
        patterns = {
            "METRIC_PHRASES": rf"\b(?:{alternatives(words['metric_phrases'])})\b",
            "UNREAD_WORDS": rf"\b({alternatives(words['unreadable'])})\b",
            "FY_QUARTER": rf"\b(?:{fy})\s*q(?P<q>[1-4])(?:\s*(?P<a>\d{{4}})\s*[-/]\s*(?P<b>\d{{2,4}})|\s*(?P<short>\d\d))?\b",
            "FY_RANGE": rf"\b(?:(?:{fy})\s*)?(?P<a>{YEAR})\s*[-/]\s*(?P<b>\d{{2,4}})\b",
            "FY_SHORT": rf"\b(?:{fy})\s*(?P<short>\d\d)\b",
            "FY_RELATIVE": rf"\b(?P<which>{this}|{last})\s+(?:{fy})\b",
            "QUARTER_NUMBER": rf"\bq(?P<q>[1-4])(?:\s+(?P<year>{YEAR})\b)?",
            "QUARTER_ORDINAL": rf"\b(?P<ord>first|second|third|fourth)\s+quarter(?:\s+(?P<year>{YEAR})\b)?",
            "QUARTER_RELATIVE": rf"\b(?P<which>{this}|{last})\s+quarter\b",
            "HALF_NUMBER": rf"\bh(?P<h>[12])(?:\s+(?P<year>{YEAR})\b)?",
            "HALF_ORDINAL": rf"\b(?P<ord>first|second)\s+half(?:\s+(?P<year>{YEAR})\b)?",
            "LAST_N": rf"\b(?:{last})\s+(?P<n>\d+|{"|".join(NUMBER_WORDS)})\s+(?P<unit>day|week|month|year)s?\b",
            "YEAR_TO_DATE": rf"\b(?:{alternatives(words['year_to_date'])})\b",
            "MONTH_TO_DATE": rf"\b(?:{alternatives(words['month_to_date'])})\b",
            "SINCE_MONTH": rf"\bsince\s+(?P<month>{MONTH_NAMES})\b(?:\s+(?P<year>{YEAR})\b)?",
            "RANGE": rf"\b(?:(?:{between})\s+{month}\s+(?:{to}|{and_})|(?:from\s+)?{month}\s+(?:{to}))\s+{month}\b",
            "MONTH_LIST": rf"\b{month}(?:\s*,\s*{month})+(?:\s*,?\s*(?:{and_})\s+{month})?\b",
            "MONTH_MENTION": rf"\b(?P<month>{MONTH_NAMES})\b(?:\s+(?P<year>{YEAR})\b)?(?P<last_year>\s+last\s+year\b)?",
            "LAST_MONTH": rf"\b(?:{last})\s+month\b",
            "THIS_MONTH": rf"\b(?:{this})\s+month\b",
            "LAST_YEAR": rf"\b(?:{last})\s+year\b",
            "THIS_YEAR": rf"\b(?:{this})\s+year\b",
            "BARE_YEAR": rf"\b(?P<year>{YEAR})\b",
        }
        return {name: re.compile(pattern) for name, pattern in patterns.items()}

    def correct_typos(self, text: str) -> str:
        def fix(found: re.Match) -> str:
            word = found.group(0)
            if word in self.vocabulary:
                return word
            close = difflib.get_close_matches(word, self.vocabulary, n=1, cutoff=FUZZY_CUTOFF)
            return close[0] if close else word
        return re.sub(rf"[a-z]{{{FUZZY_MIN_LENGTH},}}", fix, text)

    def execute(self, text: str, today: date, against: str | None = None) -> Period:
        periods = self.read_all(text, today, against)
        if not periods:
            return self.last_finished_month(today)
        if len(periods) > 1:
            raise PeriodNotSupported([period.label for period in periods], "more than one period")
        if periods[0].start > today:
            raise PeriodNotSupported([periods[0].label], "a period that has not started")
        return periods[0]

    def each(self, text: str, today: date, against: str | None = None) -> list[Period]:
        periods = self.read_all(text, today, against)
        for period in periods:
            if period.start > today:
                raise PeriodNotSupported([period.label], "a period that has not started")
        return periods

    def pair(self, text: str, today: date, against: str | None = None) -> tuple[Period, Period] | None:
        periods = self.read_all(text, today, against)
        if len(periods) != 2:
            return None
        for period in periods:
            if period.start > today:
                raise PeriodNotSupported([period.label], "a period that has not started")
        return periods[0], periods[1]

    def read_all(self, text: str, today: date, against: str | None) -> list[Period]:
        lowered = self.correct_typos(text.lower())
        dates = [found.group(0) for found in DATE.finditer(lowered)]
        remaining = DATE.sub(" ", lowered)
        remaining = self.patterns["METRIC_PHRASES"].sub(" ", remaining)
        mentions: list[Mention] = []
        for pattern, build in self.readers():
            def take(found: re.Match) -> str:
                mentions.append(build(found, today))
                return " " * len(found.group(0))
            remaining = pattern.sub(take, remaining)
        fallback_mentions, unsupported = self.read_with_fallback(remaining, today)
        mentions += fallback_mentions
        for _, phrase in unsupported:
            remaining = remaining.replace(phrase, " ")
        unread = dates + [phrase for _, phrase in unsupported] + [found.group(0) for found in self.unreadable.finditer(remaining)]
        if unread:
            raise PeriodNotSupported(unread, "time words that cannot be read")
        mentions = self.without_comparison_base(mentions, against)
        return list(dict.fromkeys(mention.period for mention in mentions))

    def read_with_fallback(self, remaining: str, today: date) -> tuple[list[Mention], list[tuple[str, str]]]:
        if self.fallback is None or not remaining.strip():
            return [], []
        mentions, unsupported = [], []
        for found in self.fallback.find(remaining, today):
            if found.grain in ("month", "year"):
                period = self.month(found.day.year, found.day.month, today) if found.grain == "month" else self.year(found.day.year, today)
                mentions.append(Mention(replace(period, note=f"I read \u201c{found.text}\u201d as {period.label}."), None))
            else:
                unsupported.append((found.grain, found.text))
        return mentions, unsupported

    def readers(self):
        return [
            (self.patterns["FY_QUARTER"], self.fy_quarter),
            (self.patterns["FY_RANGE"], self.fy_range),
            (self.patterns["FY_SHORT"], self.fy_short),
            (self.patterns["FY_RELATIVE"], self.fy_relative),
            (self.patterns["QUARTER_NUMBER"], lambda f, t: self.quarter(int(f.group("q")), f.group("year"), t)),
            (self.patterns["QUARTER_ORDINAL"], lambda f, t: self.quarter(ORDINALS[f.group("ord")], f.group("year"), t)),
            (self.patterns["QUARTER_RELATIVE"], self.quarter_relative),
            (self.patterns["HALF_NUMBER"], lambda f, t: self.half(int(f.group("h")), f.group("year"), t)),
            (self.patterns["HALF_ORDINAL"], lambda f, t: self.half(ORDINALS[f.group("ord")], f.group("year"), t)),
            (self.patterns["LAST_N"], self.last_n),
            (self.patterns["MONTH_TO_DATE"], lambda f, t: Mention(self.month(t.year, t.month, t), None)),
            (self.patterns["YEAR_TO_DATE"], lambda f, t: Mention(self.year(t.year, t), None)),
            (self.patterns["SINCE_MONTH"], self.since),
            (self.patterns["RANGE"], self.month_range),
            (self.patterns["MONTH_LIST"], self.month_range),
            (self.patterns["MONTH_MENTION"], self.named_month),
            (self.patterns["LAST_MONTH"], self.last_month),
            (self.patterns["THIS_MONTH"], lambda f, t: Mention(self.month(t.year, t.month, t), None)),
            (self.patterns["LAST_YEAR"], lambda f, t: Mention(self.year(t.year - 1, t), "last_year_alone")),
            (self.patterns["THIS_YEAR"], lambda f, t: Mention(self.year(t.year, t), None)),
            (self.patterns["BARE_YEAR"], lambda f, t: Mention(self.year(int(f.group("year")), t), None)),
        ]

    def without_comparison_base(self, mentions: list[Mention], against: str | None) -> list[Mention]:
        base = {"last_year": "last_year_alone", "previous": "last_month"}.get(against)
        if base is None:
            return mentions
        kept = [mention for mention in mentions if mention.bare != base]
        return kept or mentions

    def named_month(self, found: re.Match, today: date) -> Mention:
        month = MONTHS[found.group("month")]
        if found.group("year"):
            year = int(found.group("year"))
        elif found.group("last_year"):
            year = today.year - 1
        else:
            year = today.year if month <= today.month else today.year - 1
        return Mention(self.month(year, month, today), None)

    def month_range(self, found: re.Match, today: date) -> Mention:
        text = found.group(0)
        words = [m for m in self.patterns["MONTH_MENTION"].finditer(text)]
        months = [self.named_month(m, today).period for m in words]
        if len(months) == 2 and months[0].start > months[1].start and not re.search(YEAR, text):
            months[0] = self.month(months[0].year - 1, months[0].month, today)
        first = min(months, key=lambda m: m.start)
        last = max(months, key=lambda m: m.start)
        end = date(last.year, last.month, calendar.monthrange(last.year, last.month)[1])
        return Mention(self.span(first.start, end, today, self.range_label(first, last)), None)

    def range_label(self, first: Period, last: Period) -> str:
        if first.year == last.year:
            return f"{calendar.month_name[first.month]} to {calendar.month_name[last.month]} {last.year}"
        return f"{first.label} to {last.label}"

    def last_month(self, found: re.Match, today: date) -> Mention:
        first = today.replace(day=1) - timedelta(days=1)
        return Mention(self.month(first.year, first.month, today), "last_month")

    def since(self, found: re.Match, today: date) -> Mention:
        month = MONTHS[found.group("month")]
        year = int(found.group("year")) if found.group("year") else (today.year if month <= today.month else today.year - 1)
        start = date(year, month, 1)
        return Mention(self.span(start, today, today, f"{calendar.month_name[month]} {year} to date"), None)

    def last_n(self, found: re.Match, today: date) -> Mention:
        number, unit = found.group("n"), found.group("unit")
        count = int(number) if number.isdigit() else NUMBER_WORDS[number]
        if unit in UNIT_DAYS:
            start = today - timedelta(days=count * UNIT_DAYS[unit] - 1)
            return Mention(self.span(start, today, today, f"the last {count} {unit}s"), None)
        months = count * (12 if unit == "year" else 1)
        first = self.shift_months(today.replace(day=1), -months)
        end = today.replace(day=1) - timedelta(days=1)
        return Mention(self.span(first, end, today, f"the last {count} {unit}s"), None)

    def quarter(self, number: int, year_text: str | None, today: date) -> Mention:
        start_month = 3 * number - 2
        year = int(year_text) if year_text else (today.year if start_month <= today.month else today.year - 1)
        return Mention(self.months_span(year, start_month, 3, today, f"Q{number} {year}"), None)

    def half(self, number: int, year_text: str | None, today: date) -> Mention:
        start_month = 6 * number - 5
        year = int(year_text) if year_text else (today.year if start_month <= today.month else today.year - 1)
        return Mention(self.months_span(year, start_month, 6, today, f"H{number} {year}"), None)

    def quarter_relative(self, found: re.Match, today: date) -> Mention:
        start = date(today.year, 3 * ((today.month - 1) // 3) + 1, 1)
        if found.group("which") in ("last", "previous"):
            start = self.shift_months(start, -3)
        number = (start.month - 1) // 3 + 1
        return Mention(self.months_span(start.year, start.month, 3, today, f"Q{number} {start.year}"), None)

    def fy_quarter(self, found: re.Match, today: date) -> Mention:
        number = int(found.group("q"))
        if found.group("a"):
            first = int(found.group("a"))
        elif found.group("short"):
            first = 2000 + int(found.group("short")) - 1
        else:
            first = self.current_fy(today)
        start = self.shift_months(date(first, 4, 1), 3 * (number - 1))
        return Mention(self.months_span(start.year, start.month, 3, today, f"{self.fy_label(first)} Q{number}"), None)

    def fy_range(self, found: re.Match, today: date) -> Mention:
        first = int(found.group("a"))
        return Mention(self.fy(first, today), None)

    def fy_short(self, found: re.Match, today: date) -> Mention:
        return Mention(self.fy(2000 + int(found.group("short")) - 1, today), None)

    def fy_relative(self, found: re.Match, today: date) -> Mention:
        first = self.current_fy(today) - (1 if found.group("which") in ("last", "previous") else 0)
        return Mention(self.fy(first, today), None)

    def fy(self, first: int, today: date) -> Period:
        return self.months_span(first, 4, 12, today, self.fy_label(first))

    def fy_label(self, first: int) -> str:
        return f"FY {first}-{str(first + 1)[-2:]}"

    def current_fy(self, today: date) -> int:
        return today.year if today.month >= 4 else today.year - 1

    def months_span(self, year: int, month: int, count: int, today: date, label: str) -> Period:
        start = date(year, month, 1)
        return self.span(start, self.shift_months(start, count) - timedelta(days=1), today, label)

    def span(self, start: date, end: date, today: date, label: str) -> Period:
        return Period("span", start.year, start.month, start, min(end, today), end < today, label)

    def shift_months(self, day: date, months: int) -> date:
        index = day.year * 12 + day.month - 1 + months
        return date(index // 12, index % 12 + 1, 1)

    def last_finished_month(self, today: date) -> Period:
        last = today.replace(day=1) - timedelta(days=1)
        period = self.month(last.year, last.month, today)
        return replace(period, note=f"No period was named, so this is {period.label}.")

    def month(self, year: int, month: int, today: date) -> Period:
        start = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        return Period("month", year, month, start, min(last_day, today), last_day < today, f"{calendar.month_name[month]} {year}")

    def year(self, year: int, today: date) -> Period:
        last_day = date(year, 12, 31)
        return Period("year", year, None, date(year, 1, 1), min(last_day, today), last_day < today, str(year))
