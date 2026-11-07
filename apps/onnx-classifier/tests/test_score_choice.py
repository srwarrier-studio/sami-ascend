import math

import pytest
from fakes import FakePairScorer

from onnx_classifier.application.score_choice import ScoreChoice
from onnx_classifier.domain.errors import InvalidQuestion

CHOICES = {"Sales": "sales, revenue", "Finance": "receivables, cash", "Other": "everything else"}


class TestProbabilities:
    def test_the_highest_logit_gets_the_highest_probability_and_they_sum_to_one(self):
        result = ScoreChoice(FakePairScorer([3.0, 0.5, -1.0]), 1.0).execute("q", "Which?", CHOICES)
        assert max(result, key=result.get) == "Sales"
        assert math.isclose(sum(result.values()), 1.0)

    def test_a_higher_temperature_makes_the_answer_less_confident(self):
        sharp = ScoreChoice(FakePairScorer([3.0, 0.5, -1.0]), 1.0).execute("q", "Which?", CHOICES)
        soft = ScoreChoice(FakePairScorer([3.0, 0.5, -1.0]), 2.0).execute("q", "Which?", CHOICES)
        assert soft["Sales"] < sharp["Sales"]

    def test_very_large_logits_do_not_overflow(self):
        result = ScoreChoice(FakePairScorer([900.0, 899.0, 0.0]), 1.0).execute("q", "Which?", CHOICES)
        assert math.isclose(sum(result.values()), 1.0)

    def test_one_option_is_certain(self):
        assert ScoreChoice(FakePairScorer([0.2]), 1.0).execute("q", "Which?", {"Only": "the one"}) == {"Only": 1.0}


class TestWhatTheScorerSees:
    def test_each_option_text_has_the_instructions_name_and_description(self):
        scorer = FakePairScorer([1.0, 0.0, 0.0])
        ScoreChoice(scorer, 1.0).execute("how much did we sell", "Which department?", CHOICES)
        question, options = scorer.calls[0]
        assert question == "how much did we sell"
        assert options[0] == "Which department? Sales: sales, revenue"
        assert len(options) == 3


class TestInvalidQuestion:
    def test_no_options_is_refused(self):
        with pytest.raises(InvalidQuestion):
            ScoreChoice(FakePairScorer([]), 1.0).execute("q", "Which?", {})
