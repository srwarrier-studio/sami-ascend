import calendar
import re
from dataclasses import dataclass
from datetime import date, timedelta

from intent_api.domain.entities.period import Period
from intent_api.domain.errors import PeriodNotSupported

MONTHS = {name.lower(): number for number, name in enumerate(calendar.month_name) if name}
MONTHS.update({name.lower(): number for number, name in enumerate(calendar.month_abbr) if name})
MONTHS["sept"] = 9

MENTION = re.compile(
    r"\b(?P<month>" + "|".join(sorted(MONTHS, key=len, reverse=True)) + r")\b(?:\s+(?P<year>(?:19|20)\d\d)\b)?(?P<last_year>\s+last\s+year\b)?"
    r"|\b(?P<last_month>last\s+month)\b"
    r"|\b(?P<this_month>this\s+month)\b"
    r"|\b(?P<last_year_alone>last\s+year)\b"
    r"|\b(?P<this_year>this\s+year)\b"
    r"|\b(?P<bare_year>(?:19|20)\d\d)\b"
)


@dataclass(frozen=True)
class Mention:
    period: Period
    bare: str | None


class ReadPeriod:
    def execute(self, text: str, today: date, against: str | None = None) -> Period:
        mentions = [self.mention(found, today) for found in MENTION.finditer(text.lower())]
        mentions = self.without_comparison_base(mentions, against)
        periods = list(dict.fromkeys(mention.period for mention in mentions))
        if not periods:
            return self.last_finished_month(today)
        if len(periods) > 1:
            raise PeriodNotSupported([period.label for period in periods], "more than one period")
        if periods[0].start > today:
            raise PeriodNotSupported([periods[0].label], "a period that has not started")
        return periods[0]

    def without_comparison_base(self, mentions: list[Mention], against: str | None) -> list[Mention]:
        base = {"last_year": "last_year_alone", "previous": "last_month"}.get(against)
        if base is None:
            return mentions
        kept = [mention for mention in mentions if mention.bare != base]
        return kept or mentions

    def mention(self, found: re.Match, today: date) -> Mention:
        if found.group("month"):
            month = MONTHS[found.group("month")]
            if found.group("year"):
                year = int(found.group("year"))
            elif found.group("last_year"):
                year = today.year - 1
            else:
                year = today.year if month <= today.month else today.year - 1
            return Mention(self.month(year, month, today), None)
        if found.group("last_month"):
            first = today.replace(day=1) - timedelta(days=1)
            return Mention(self.month(first.year, first.month, today), "last_month")
        if found.group("this_month"):
            return Mention(self.month(today.year, today.month, today), None)
        if found.group("last_year_alone"):
            return Mention(self.year(today.year - 1, today), "last_year_alone")
        if found.group("this_year"):
            return Mention(self.year(today.year, today), None)
        return Mention(self.year(int(found.group("bare_year")), today), None)

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
