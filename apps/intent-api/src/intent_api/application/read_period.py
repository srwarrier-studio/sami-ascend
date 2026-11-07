import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta

from intent_api.domain.entities.period import Period
from intent_api.domain.errors import PeriodNotSupported

MONTHS = {name.lower(): number for number, name in enumerate(calendar.month_name) if name}
MONTHS.update({name.lower(): number for number, name in enumerate(calendar.month_abbr) if name})
MONTHS["sept"] = 9
MONTH_NAMES = "|".join(sorted(MONTHS, key=len, reverse=True))
ORDINALS = {"first": 1, "second": 2, "third": 3, "fourth": 4}
UNIT_DAYS = {"day": 1, "week": 7}
YEAR = r"(?:19|20)\d\d"

UNREAD_WORDS = re.compile(r"\b(yesterday|today|tonight|tomorrow|weekly|daily|weekend|weekday|week|day)\b")
DATE = re.compile(r"\b\d{1,2}[/.-]\d{1,2}[/.-]\d{2,4}\b")

FY_QUARTER = re.compile(rf"\bfy\s*q(?P<q>[1-4])(?:\s*(?P<a>\d{{4}})\s*[-/]\s*(?P<b>\d{{2,4}})|\s*(?P<short>\d\d))?\b")
FY_RANGE = re.compile(rf"\b(?:(?:fy|financial\s+year)\s*)?(?P<a>{YEAR})\s*[-/]\s*(?P<b>\d{{2,4}})\b")
FY_SHORT = re.compile(r"\bfy\s*(?P<short>\d\d)\b")
FY_RELATIVE = re.compile(r"\b(?P<which>this|current|last|previous)\s+(?:fy|financial\s+year|fiscal\s+year)\b")
QUARTER_NUMBER = re.compile(rf"\bq(?P<q>[1-4])(?:\s+(?P<year>{YEAR})\b)?")
QUARTER_ORDINAL = re.compile(rf"\b(?P<ord>first|second|third|fourth)\s+quarter(?:\s+(?P<year>{YEAR})\b)?")
QUARTER_RELATIVE = re.compile(r"\b(?P<which>this|current|last|previous)\s+quarter\b")
HALF_NUMBER = re.compile(rf"\bh(?P<h>[12])(?:\s+(?P<year>{YEAR})\b)?")
HALF_ORDINAL = re.compile(rf"\b(?P<ord>first|second)\s+half(?:\s+(?P<year>{YEAR})\b)?")
LAST_N = re.compile(r"\b(?:last|past|previous)\s+(?P<n>\d+)\s+(?P<unit>day|week|month|year)s?\b")
YEAR_TO_DATE = re.compile(r"\b(?:ytd|year\s+to\s+date|so\s+far\s+this\s+year|till\s+date|to\s+date|so\s+far)\b")
MONTH_TO_DATE = re.compile(r"\b(?:mtd|month\s+to\s+date|so\s+far\s+this\s+month)\b")
SINCE_MONTH = re.compile(rf"\bsince\s+(?P<month>{MONTH_NAMES})\b(?:\s+(?P<year>{YEAR})\b)?")
MONTH_MENTION = re.compile(rf"\b(?P<month>{MONTH_NAMES})\b(?:\s+(?P<year>{YEAR})\b)?(?P<last_year>\s+last\s+year\b)?")
LAST_MONTH = re.compile(r"\b(?:last|previous|prior)\s+month\b")
THIS_MONTH = re.compile(r"\b(?:this|current|present)\s+month\b")
LAST_YEAR = re.compile(r"\b(?:last|previous|prior)\s+year\b")
THIS_YEAR = re.compile(r"\b(?:this|current|present)\s+year\b")
BARE_YEAR = re.compile(rf"\b(?P<year>{YEAR})\b")


@dataclass(frozen=True)
class Mention:
    period: Period
    bare: str | None


class ReadPeriod:
    def execute(self, text: str, today: date, against: str | None = None) -> Period:
        lowered = text.lower()
        dates = [found.group(0) for found in DATE.finditer(lowered)]
        remaining = DATE.sub(" ", lowered)
        mentions: list[Mention] = []
        for pattern, build in self.readers():
            def take(found: re.Match) -> str:
                mentions.append(build(found, today))
                return " " * len(found.group(0))
            remaining = pattern.sub(take, remaining)
        unread = dates + [found.group(0) for found in UNREAD_WORDS.finditer(remaining)]
        if unread:
            raise PeriodNotSupported(unread, "time words that cannot be read")
        mentions = self.without_comparison_base(mentions, against)
        periods = list(dict.fromkeys(mention.period for mention in mentions))
        if not periods:
            return self.last_finished_month(today)
        if len(periods) > 1:
            raise PeriodNotSupported([period.label for period in periods], "more than one period")
        if periods[0].start > today:
            raise PeriodNotSupported([periods[0].label], "a period that has not started")
        return periods[0]

    def readers(self):
        return [
            (FY_QUARTER, self.fy_quarter),
            (FY_RANGE, self.fy_range),
            (FY_SHORT, self.fy_short),
            (FY_RELATIVE, self.fy_relative),
            (QUARTER_NUMBER, lambda f, t: self.quarter(int(f.group("q")), f.group("year"), t)),
            (QUARTER_ORDINAL, lambda f, t: self.quarter(ORDINALS[f.group("ord")], f.group("year"), t)),
            (QUARTER_RELATIVE, self.quarter_relative),
            (HALF_NUMBER, lambda f, t: self.half(int(f.group("h")), f.group("year"), t)),
            (HALF_ORDINAL, lambda f, t: self.half(ORDINALS[f.group("ord")], f.group("year"), t)),
            (LAST_N, self.last_n),
            (MONTH_TO_DATE, lambda f, t: Mention(self.month(t.year, t.month, t), None)),
            (YEAR_TO_DATE, lambda f, t: Mention(self.year(t.year, t), None)),
            (SINCE_MONTH, self.since),
            (MONTH_MENTION, self.named_month),
            (LAST_MONTH, self.last_month),
            (THIS_MONTH, lambda f, t: Mention(self.month(t.year, t.month, t), None)),
            (LAST_YEAR, lambda f, t: Mention(self.year(t.year - 1, t), "last_year_alone")),
            (THIS_YEAR, lambda f, t: Mention(self.year(t.year, t), None)),
            (BARE_YEAR, lambda f, t: Mention(self.year(int(f.group("year")), t), None)),
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

    def last_month(self, found: re.Match, today: date) -> Mention:
        first = today.replace(day=1) - timedelta(days=1)
        return Mention(self.month(first.year, first.month, today), "last_month")

    def since(self, found: re.Match, today: date) -> Mention:
        month = MONTHS[found.group("month")]
        year = int(found.group("year")) if found.group("year") else (today.year if month <= today.month else today.year - 1)
        start = date(year, month, 1)
        return Mention(self.span(start, today, today, f"{calendar.month_name[month]} {year} to date"), None)

    def last_n(self, found: re.Match, today: date) -> Mention:
        count, unit = int(found.group("n")), found.group("unit")
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
        return self.month(last.year, last.month, today)

    def month(self, year: int, month: int, today: date) -> Period:
        start = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
        return Period("month", year, month, start, min(last_day, today), last_day < today, f"{calendar.month_name[month]} {year}")

    def year(self, year: int, today: date) -> Period:
        last_day = date(year, 12, 31)
        return Period("year", year, None, date(year, 1, 1), min(last_day, today), last_day < today, str(year))
