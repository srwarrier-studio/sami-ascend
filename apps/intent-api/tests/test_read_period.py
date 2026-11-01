from datetime import date

import pytest

from intent_api.application.read_period import ReadPeriod
from intent_api.domain.errors import PeriodNotSupported

TODAY = date(2026, 11, 15)


def read(text, against=None):
    return ReadPeriod().execute(text, TODAY, against)


def refused(text, against=None) -> PeriodNotSupported:
    with pytest.raises(PeriodNotSupported) as error:
        read(text, against)
    return error.value


class TestMonths:
    def test_a_month_name_is_the_latest_one_not_in_the_future(self):
        period = read("to whom did we sell the most in June")
        assert (period.kind, period.year, period.month, period.label) == ("month", 2026, 6, "June 2026")
        assert (period.start, period.end, period.complete) == (date(2026, 6, 1), date(2026, 6, 30), True)

    def test_a_month_later_in_the_year_than_today_is_last_year(self):
        assert read("sales in december").label == "December 2025"

    def test_an_explicit_year_wins(self):
        assert read("sales in March 2024").label == "March 2024"

    def test_a_month_followed_by_last_year_is_that_month_of_last_year(self):
        assert read("sales in March last year").label == "March 2025"

    def test_abbreviations_are_read(self):
        assert [read(f"sales in {name}").month for name in ("jun", "sept", "Oct")] == [6, 9, 10]

    def test_the_current_month_is_incomplete_and_ends_today(self):
        period = read("sales in november")
        assert (period.complete, period.end) == (False, TODAY)


class TestRelativePeriods:
    def test_last_month(self):
        period = read("how were sales last month")
        assert (period.label, period.complete) == ("October 2026", True)

    def test_last_month_across_a_year_end(self):
        assert ReadPeriod().execute("sales last month", date(2026, 1, 10)).label == "December 2025"

    def test_this_month_is_incomplete(self):
        period = read("sales this month")
        assert (period.label, period.complete, period.end) == ("November 2026", False, TODAY)

    def test_last_year_is_the_whole_year(self):
        period = read("sales last year")
        assert (period.kind, period.label, period.start, period.end) == ("year", "2025", date(2025, 1, 1), date(2025, 12, 31))

    def test_this_year_runs_to_today(self):
        period = read("sales this year")
        assert (period.kind, period.complete, period.end) == ("year", False, TODAY)

    def test_a_year_alone(self):
        assert read("purchases in 2024").label == "2024"


class TestNoPeriod:
    def test_the_last_finished_month_is_used(self):
        period = read("who are our top customers")
        assert (period.label, period.complete) == ("October 2026", True)

    def test_a_number_that_is_not_a_year_is_ignored(self):
        assert read("our top 5 customers").label == "October 2026"

    def test_a_word_that_only_contains_a_month_is_ignored(self):
        assert read("sales of marching bands and decorations").label == "October 2026"


class TestRefusals:
    def test_two_months(self):
        error = refused("sales in June and in May")
        assert error.periods == ["June 2026", "May 2026"]
        assert error.reason == "more than one period"

    def test_a_month_and_a_year(self):
        assert refused("sales in June 2026 and 2025").periods == ["June 2026", "2025"]

    def test_the_same_period_twice_is_one_period(self):
        assert read("sales in june, yes june").label == "June 2026"

    def test_a_period_in_the_future(self):
        error = refused("sales in december 2026")
        assert (error.periods, error.reason) == (["December 2026"], "a period that has not started")

    def test_next_year_is_in_the_future(self):
        assert refused("sales in 2027").periods == ["2027"]


class TestComparisonBase:
    def test_last_year_is_the_base_when_a_month_is_named(self):
        assert read("sales in March compared with last year", "last_year").label == "March 2026"

    def test_last_year_alone_is_the_period_when_it_is_all_that_is_named(self):
        assert read("how do sales compare with last year", "last_year").label == "2025"

    def test_last_month_is_the_base_of_a_comparison_with_the_previous_period(self):
        assert read("sales in June against last month", "previous").label == "June 2026"

    def test_a_named_month_of_last_year_is_still_a_period(self):
        assert read("sales in March last year", "last_year").label == "March 2025"

    def test_without_a_comparison_last_year_is_a_period(self):
        assert refused("sales in March compared with last year").periods == ["March 2026", "2025"]
