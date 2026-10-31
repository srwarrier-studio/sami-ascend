from datetime import date

import pytest

from sami_agents.application.model_checks import accept_question, accept_rewrite, risky_tokens
from sami_agents.domain.entities.question import Question

TODAY = date(2026, 10, 31)
METRICS = ["sales", "purchases"]
ORIGINAL = "Sales fell 14.4% from July 2026 to August 2026 (INR 7,570,000 to INR 6,480,000)."


class TestAcceptQuestion:
    def test_a_valid_answer_is_accepted(self):
        assert accept_question({"metric": "sales", "direction": "fall", "month": "2026-08"}, METRICS, TODAY) == Question("sales", "fall", date(2026, 8, 1))

    @pytest.mark.parametrize(
        "data",
        [
            None, "sales", [], {},
            {"metric": "weather", "direction": "fall", "month": "2026-08"},
            {"metric": "sales", "direction": "sideways", "month": "2026-08"},
            {"metric": "sales", "direction": "fall", "month": "2026-13"},
            {"metric": "sales", "direction": "fall", "month": "August"},
            {"metric": "sales", "direction": "fall", "month": "2026-10"},
            {"metric": "sales", "direction": "fall", "month": "2027-01"},
            {"metric": "sales", "direction": "fall"},
        ],
    )
    def test_anything_else_is_refused(self, data):
        assert accept_question(data, METRICS, TODAY) is None


class TestAcceptRewrite:
    def test_a_rewrite_that_keeps_every_figure_and_name_is_accepted(self):
        text = "Sales dropped by 14.4% between July 2026 and August 2026, from INR 7,570,000 to INR 6,480,000."
        assert accept_rewrite(text, ORIGINAL) == text

    @pytest.mark.parametrize(
        "candidate",
        [
            "Sales fell 15% from July 2026 to August 2026.",
            "Sales fell 14.4% in August 2026 because of Acme.",
            "Sales fell 14.4% from July 2026 to August 2026 (INR 7,570,000 to INR 6,480,001).",
            "Sales fell.\nAnd more.",
            "x" * 400,
            "",
            None,
        ],
    )
    def test_one_that_adds_a_figure_a_name_a_line_or_length_is_dropped(self, candidate):
        assert accept_rewrite(candidate, ORIGINAL) is None

    @pytest.mark.parametrize(
        "candidate",
        [
            "Sales fell 14.4% from July to August (INR 7,570,000 to INR 6,480,000).",
            "Sales fell 14.4% from July 2026 to August 2026.",
            "Great news! Sales fell 14.4% from July 2026 to August 2026 (INR 7,570,000 to INR 6,480,000).",
            "**Sales** fell 14.4% from July 2026 to August 2026 (INR 7,570,000 to INR 6,480,000).",
            "Sales fell 14.4% from July 2026 to August 2026 (INR 7,570,000 to INR 6,480,000) and that is very, very, very much worse than anyone had hoped for, and it is the kind of thing we should look at closely.",
        ],
    )
    def test_one_that_drops_a_figure_uses_markup_or_runs_long_is_dropped(self, candidate):
        assert accept_rewrite(candidate, ORIGINAL) is None

    def test_a_name_in_other_case_still_counts_as_kept(self):
        assert accept_rewrite("acme industries fell 10%", "Acme Industries fell 10%") is not None

    def test_the_risky_tokens_are_numbers_and_names_after_the_first_word(self):
        assert risky_tokens(ORIGINAL) >= {"14.4%", "July", "2026", "August", "INR", "7,570,000", "6,480,000"}
        assert "Sales" not in risky_tokens(ORIGINAL)


class TestTheMeaningIsKept:
    @pytest.mark.parametrize(
        "original,candidate",
        [
            ("This coincided with no valid contract for 50 days from 2026-07-13 (contract 0040000127).", "This coincided with a valid contract for 50 days from 2026-07-13 (contract 0040000127)."),
            ("Sales were steady: they fell 3.6% from July 2026 to August 2026.", "Sales fell 3.6% from July 2026 to August 2026."),
            ("Acme Industries fell 97.8% (INR 881,583), 80.2% of the change.", "Acme Industries fell 97.8% (INR 881,583), marking an 80.2% change in the value."),
            ("Bearing 6204 offset part of it: rose 20.8%.", "Bearing 6204 offset rose 20.8%."),
            ("This coincided with delivery 1 being late, and behind that order 2, and behind that product RM-1.", "This coincided with delivery 1 being late and order 2 and product RM-1."),
            ("Overall the month was steady; the movements above are the ones with something behind them in the data we hold.", "Overall the month was steady; movements above are influenced by data."),
        ],
    )
    def test_a_rewrite_that_inverts_drops_or_restates_is_dropped(self, original, candidate):
        assert accept_rewrite(candidate, original) is None

    @pytest.mark.parametrize(
        "original,candidate",
        [
            ("Acme Industries fell 97.8% (INR 881,583), 80.2% of the change.", "Acme Industries fell 97.8% (INR 881,583), accounting for 80.2% of the change."),
            ("Nothing unusual was found behind this month.", "No unusual cause was found behind this month."),
            ("Purchases were steady: they rose 2.4% from July 2026 to August 2026.", "Purchases remained steady: they rose 2.4% from July 2026 to August 2026."),
        ],
    )
    def test_a_faithful_rewrite_is_kept(self, original, candidate):
        assert accept_rewrite(candidate, original) == candidate
