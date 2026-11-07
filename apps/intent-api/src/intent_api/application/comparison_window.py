import calendar
from datetime import date, timedelta

from intent_api.domain.entities.figures import Window
from intent_api.domain.entities.period import Period


def comparison_window(period: Period, against: str | None, base: Period | None = None) -> Window:
    if base is not None:
        return Window(period.start, period.end, base.start, base.end if period.complete else min(base.end, base.start + (period.end - period.start)))
    if period.kind == "year":
        start = date(period.year - 1, 1, 1)
        last_day = date(period.year - 1, 12, 31)
    elif period.kind == "span":
        return span_window(period, against)
    else:
        year, month = (period.year - 1, period.month) if against == "last_year" else previous_month(period.year, period.month)
        start = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
    return Window(period.start, period.end, start, min(last_day, start + (period.end - period.start)))


def previous_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)


def span_window(period: Period, against: str | None) -> Window:
    length = period.end - period.start
    if against == "last_year":
        start = date(period.start.year - 1, period.start.month, period.start.day)
    elif period.start.day == 1:
        months = (period.end.year - period.start.year) * 12 + period.end.month - period.start.month + 1
        index = period.start.year * 12 + period.start.month - 1 - months
        start = date(index // 12, index % 12 + 1, 1)
    else:
        start = period.start - length - timedelta(days=1)
    full_end = period.start - timedelta(days=1) if against != "last_year" and period.start.day == 1 else start + length
    return Window(period.start, period.end, start, min(full_end, start + length) if not period.complete else full_end)
