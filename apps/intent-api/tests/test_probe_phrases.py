from datetime import date

import pytest

from intent_api.domain.errors import PeriodNotSupported
from tests.fakes import period_reader

TODAY = date(2026, 11, 7)

READ = [
    ("sales current month", "November 2026", date(2026, 11, 1), TODAY),
    ("sales present month", "November 2026", date(2026, 11, 1), TODAY),
    ("sales previous month", "October 2026", date(2026, 10, 1), date(2026, 10, 31)),
    ("sales MTD", "November 2026", date(2026, 11, 1), TODAY),
    ("sales month to date", "November 2026", date(2026, 11, 1), TODAY),
    ("sales YTD", "2026", date(2026, 1, 1), TODAY),
    ("sales year to date", "2026", date(2026, 1, 1), TODAY),
    ("sales current year", "2026", date(2026, 1, 1), TODAY),
    ("sales so far this year", "2026", date(2026, 1, 1), TODAY),
    ("sales till date", "2026", date(2026, 1, 1), TODAY),
    ("sales so far", "2026", date(2026, 1, 1), TODAY),
    ("sales this financial year", "FY 2026-27", date(2026, 4, 1), TODAY),
    ("sales this quarter", "Q4 2026", date(2026, 10, 1), TODAY),
    ("sales Q3", "Q3 2026", date(2026, 7, 1), date(2026, 9, 30)),
    ("sales third quarter", "Q3 2026", date(2026, 7, 1), date(2026, 9, 30)),
    ("sales last quarter", "Q3 2026", date(2026, 7, 1), date(2026, 9, 30)),
    ("sales H1", "H1 2026", date(2026, 1, 1), date(2026, 6, 30)),
    ("sales last 30 days", "the last 30 days", date(2026, 10, 9), TODAY),
    ("sales last 3 months", "the last 3 months", date(2026, 8, 1), date(2026, 10, 31)),
    ("sales past 12 months", "the last 12 months", date(2025, 11, 1), date(2026, 10, 31)),
    ("sales FY 2025-26", "FY 2025-26", date(2025, 4, 1), date(2026, 3, 31)),
    ("sales 2025-26", "FY 2025-26", date(2025, 4, 1), date(2026, 3, 31)),
    ("sales FY26", "FY 2025-26", date(2025, 4, 1), date(2026, 3, 31)),
    ("sales FY Q3", "FY 2026-27 Q3", date(2026, 10, 1), TODAY),
    ("sales since april", "April 2026 to date", date(2026, 4, 1), TODAY),
    ("sales from april to june", "April to June 2026", date(2026, 4, 1), date(2026, 6, 30)),
    ("sales between july and september", "July to September 2026", date(2026, 7, 1), date(2026, 9, 30)),
    ("sales btw july and september", "July to September 2026", date(2026, 7, 1), date(2026, 9, 30)),
    ("sales jun, jul and aug", "June to August 2026", date(2026, 6, 1), date(2026, 8, 31)),
    ("whta is sales of current month", "November 2026", date(2026, 11, 1), TODAY),
]

REFUSED = [
    ("sales yesterday", ["yesterday"]),
    ("sales today", ["today"]),
    ("sales this week", ["week"]),
    ("sales last week", ["week"]),
    ("sales on 12/10/2026", ["12/10/2026"]),
]


class TestTheProbePhrasings:
    @pytest.mark.parametrize("text, label, start, end", READ)
    def test_each_gives_its_period(self, text, label, start, end):
        period = period_reader().execute(text, TODAY)
        assert (period.label, period.start, period.end) == (label, start, end)

    @pytest.mark.parametrize("text, words", REFUSED)
    def test_each_unread_time_word_is_refused_by_name(self, text, words):
        with pytest.raises(PeriodNotSupported) as error:
            period_reader().execute(text, TODAY)
        assert error.value.periods == words

    def test_no_period_is_assumed_and_says_so(self):
        period = period_reader().execute("how much did we sell", TODAY)
        assert (period.label, period.note) == ("October 2026", "No period was named, so this is October 2026.")

    def test_two_named_periods_are_a_pair(self):
        current, base = period_reader().pair("sales september against august", TODAY)
        assert (current.label, base.label) == ("September 2026", "August 2026")
