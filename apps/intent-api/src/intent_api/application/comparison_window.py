import calendar
from datetime import date

from intent_api.domain.entities.figures import Window
from intent_api.domain.entities.period import Period


def comparison_window(period: Period, against: str | None) -> Window:
    if period.kind == "year":
        start = date(period.year - 1, 1, 1)
        last_day = date(period.year - 1, 12, 31)
    else:
        year, month = (period.year - 1, period.month) if against == "last_year" else previous_month(period.year, period.month)
        start = date(year, month, 1)
        last_day = date(year, month, calendar.monthrange(year, month)[1])
    return Window(period.start, period.end, start, min(last_day, start + (period.end - period.start)))


def previous_month(year: int, month: int) -> tuple[int, int]:
    return (year - 1, 12) if month == 1 else (year, month - 1)
