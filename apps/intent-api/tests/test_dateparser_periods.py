from datetime import date

from intent_api.infrastructure.dateparser_periods import DateparserPeriods

TODAY = date(2026, 11, 7)


def find(text):
    return [(found.text, found.grain, found.day) for found in DateparserPeriods().find(text, TODAY)]


class TestFindingDates:
    def test_a_phrase_comes_back_with_its_grain_and_day(self):
        assert find("sales 2 months ago") == [("2 months ago", "month", date(2026, 9, 7))]

    def test_this_week_is_a_week(self):
        assert find("payments this week") == [("this week", "week", TODAY)]

    def test_a_two_letter_word_is_not_a_date(self):
        assert find("so what happened") == []

    def test_nothing_in_a_question_without_time_words(self):
        assert find("who are our top customers") == []
