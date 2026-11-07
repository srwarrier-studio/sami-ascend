from datetime import date

import pytest

from intent_api.application.read_period import ReadPeriod
from tests.fakes import period_reader
from intent_api.domain.gateways.fallback_periods import FallbackPeriods, FoundDate
from intent_api.application.read_period import ReadPeriod
from intent_api.infrastructure.period_words_loader import load_period_words
from intent_api.domain.errors import PeriodNotSupported

TODAY = date(2026, 11, 15)


def bounds(text):
    period = read(text)
    return period.label, period.start, period.end, period.complete


def read(text, against=None):
    return period_reader().execute(text, TODAY, against)


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
        assert period_reader().execute("sales last month", date(2026, 1, 10)).label == "December 2025"

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


class TestCurrentAndPreviousWording:
    @pytest.mark.parametrize("text", ["sales current month", "sales present month", "sales mtd", "sales month to date"])
    def test_the_month_so_far(self, text):
        assert bounds(text) == ("November 2026", date(2026, 11, 1), TODAY, False)

    def test_previous_month_is_last_month(self):
        assert read("sales previous month").label == "October 2026"

    @pytest.mark.parametrize("text", ["sales ytd", "sales year to date", "sales current year", "sales so far this year", "sales till date", "sales so far"])
    def test_the_year_so_far(self, text):
        assert bounds(text) == ("2026", date(2026, 1, 1), TODAY, False)


class TestQuarters:
    def test_this_quarter_runs_to_today(self):
        assert bounds("sales this quarter") == ("Q4 2026", date(2026, 10, 1), TODAY, False)

    def test_last_quarter(self):
        assert bounds("sales last quarter") == ("Q3 2026", date(2026, 7, 1), date(2026, 9, 30), True)

    def test_a_bare_quarter_is_calendar_and_the_latest_one_not_in_the_future(self):
        assert bounds("sales in Q3") == ("Q3 2026", date(2026, 7, 1), date(2026, 9, 30), True)

    def test_a_spelled_out_quarter(self):
        assert read("sales third quarter").label == "Q3 2026"

    def test_a_quarter_with_a_year(self):
        assert bounds("sales Q1 2025") == ("Q1 2025", date(2025, 1, 1), date(2025, 3, 31), True)

    def test_halves(self):
        assert [read(f"sales {name}").label for name in ("H1", "first half", "H2 2025")] == ["H1 2026", "H1 2026", "H2 2025"]


class TestFinancialYear:
    @pytest.mark.parametrize("text", ["FY 2025-26", "FY26", "2025-26", "last financial year", "last fy"])
    def test_april_to_march(self, text):
        assert bounds(f"sales {text}") == ("FY 2025-26", date(2025, 4, 1), date(2026, 3, 31), True)

    def test_this_financial_year_runs_to_today(self):
        assert bounds("sales this financial year") == ("FY 2026-27", date(2026, 4, 1), TODAY, False)

    def test_a_fiscal_quarter_needs_fy_written(self):
        assert bounds("sales FY Q3") == ("FY 2026-27 Q3", date(2026, 10, 1), TODAY, False)
        assert bounds("sales FY Q4 2025-26") == ("FY 2025-26 Q4", date(2026, 1, 1), date(2026, 3, 31), True)


class TestSinceAndLastN:
    def test_since_a_month_runs_to_today(self):
        assert bounds("sales since april") == ("April 2026 to date", date(2026, 4, 1), TODAY, False)

    def test_last_n_days(self):
        assert bounds("sales last 30 days") == ("the last 30 days", date(2026, 10, 17), TODAY, False)

    def test_last_n_months_are_whole_finished_months(self):
        assert bounds("sales past 3 months") == ("the last 3 months", date(2026, 8, 1), date(2026, 10, 31), True)


class TestUnreadTimeWords:
    @pytest.mark.parametrize("word", ["yesterday", "today", "week", "day", "12/10/2026"])
    def test_they_are_refused_by_name(self, word):
        error = refused(f"sales {word}")
        assert (error.periods, error.reason) == ([word], "time words that cannot be read")


class TestRanges:
    @pytest.mark.parametrize("text", ["from april to june", "april to june", "between april and june", "apr, may and jun"])
    def test_a_range_of_months(self, text):
        assert bounds(f"sales {text}") == ("April to June 2026", date(2026, 4, 1), date(2026, 6, 30), True)

    def test_a_range_to_the_current_month_is_incomplete(self):
        assert bounds("sales from september to november") == ("September to November 2026", date(2026, 9, 1), TODAY, False)

    def test_a_range_across_a_year_end(self):
        assert bounds("sales from november to february") == ("November 2025 to February 2026", date(2025, 11, 1), date(2026, 2, 28), True)


class TestTwoNamedPeriods:
    def test_both_are_returned_in_the_order_written(self):
        current, base = period_reader().pair("september against august", TODAY)
        assert (current.label, base.label) == ("September 2026", "August 2026")

    def test_quarters(self):
        current, base = period_reader().pair("Q2 vs Q1", TODAY)
        assert (current.label, base.label) == ("Q2 2026", "Q1 2026")

    def test_one_period_is_not_a_pair(self):
        assert period_reader().pair("sales in june", TODAY) is None

    def test_three_periods_are_not_a_pair(self):
        assert period_reader().pair("june, may versus april 2025 and 2024", TODAY) is None


class TestSpellingMistakes:
    @pytest.mark.parametrize("text", ["btw april and june", "betwen april and june", "apr thru jun"])
    def test_connectives_are_still_a_range(self, text):
        assert read(f"sales {text}").label == "April to June 2026"

    @pytest.mark.parametrize("text, label", [("sales in febuary", "February 2026"), ("sales last quater", "Q3 2026"), ("sales in novemeber", "November 2026")])
    def test_misspelt_words_are_read(self, text, label):
        assert read(text).label == label

    def test_a_name_that_only_looks_like_a_month_is_left_alone(self):
        assert read("sales to Augustine Traders").label == "October 2026"


class TestNumberWordsAndMetricNames:
    def test_the_last_six_months_with_a_spelled_number(self):
        assert bounds("sales trend for the last six month") == ("the last 6 months", date(2026, 5, 1), date(2026, 10, 31), True)

    def test_daily_sales_outstanding_is_a_metric_not_a_time_word(self):
        assert read("whats our daily sales outstanding?").label == "October 2026"


class FakeFallback(FallbackPeriods):
    def __init__(self, *found):
        self.found = list(found)
        self.seen = []

    def find(self, text, today):
        self.seen.append(text.strip())
        return self.found


def with_fallback(text, *found):
    fallback = FakeFallback(*found)
    return ReadPeriod(load_period_words(), fallback).execute(text, TODAY), fallback


class TestFallback:
    def test_it_is_asked_only_about_what_the_reader_did_not_read(self):
        _, fallback = with_fallback("sales in june gone fishing")
        assert "june" not in fallback.seen[0] and "gone fishing" in fallback.seen[0]

    def test_a_month_it_finds_is_a_month_period(self):
        period, _ = with_fallback("sales a quarter back", FoundDate("a quarter back", "month", date(2026, 8, 15)))
        assert period.label == "August 2026"

    def test_a_year_it_finds_is_a_year_period(self):
        period, _ = with_fallback("sales a while back", FoundDate("a while back", "year", date(2025, 3, 1)))
        assert period.label == "2025"

    @pytest.mark.parametrize("grain", ["day", "week", "time"])
    def test_a_day_or_a_week_is_refused_by_name(self, grain):
        with pytest.raises(PeriodNotSupported) as error:
            with_fallback("sales some day", FoundDate("some day", grain, TODAY))
        assert error.value.periods == ["some day"]


class TestNotes:
    def test_no_period_named_is_noted(self):
        assert read("who are our top customers").note == "No period was named, so this is October 2026."

    def test_a_period_named_by_the_reader_has_no_note(self):
        assert read("sales in june").note is None

    def test_a_period_found_by_the_fallback_says_which_words_were_read_as_what(self):
        period, _ = with_fallback("sales a quarter back", FoundDate("a quarter back", "month", date(2026, 8, 15)))
        assert period.note == "I read “a quarter back” as August 2026."
