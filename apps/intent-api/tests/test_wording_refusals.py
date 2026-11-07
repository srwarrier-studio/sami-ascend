from intent_api.application.wording import period_refusal


class TestPeriodRefusal:
    def test_unread_words_are_named_with_what_can_be_read(self):
        text = period_refusal("time words that cannot be read", ["today", "week"])
        assert text.startswith("I could not read “today”, “week” as a period.")
        assert "financial year" in text

    def test_a_future_period(self):
        assert period_refusal("a period that has not started", ["December 2026"]).startswith("“December 2026” has not started yet")

    def test_too_many_periods_says_how_many_are_allowed(self):
        text = period_refusal("more than 6 periods", ["a", "b", "c", "d", "e", "f", "g"])
        assert text.endswith("Ask for up to 6.")

    def test_any_other_reason_names_the_periods(self):
        assert "June 2026, May 2026" in period_refusal("more than one period", ["June 2026", "May 2026"])
