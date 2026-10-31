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

    def test_the_risky_tokens_are_numbers_and_names_after_the_first_word(self):
        assert risky_tokens(ORIGINAL) >= {"14.4%", "July", "2026", "August", "INR", "7,570,000", "6,480,000"}
        assert "Sales" not in risky_tokens(ORIGINAL)
