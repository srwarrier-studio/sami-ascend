import json

import httpx
import pytest

from intent_api.domain.entities.decision import Decision
from intent_api.domain.errors import ClassifierUnavailable
from intent_api.infrastructure.laya_choice_classifier import LayaChoiceClassifier
from intent_api.infrastructure.settings import Settings

CHOICES = {"Sales": "sales orders, revenue, customers", "Purchase": "purchases, spend, suppliers", "Other": "everything else"}


def classifier_with(handler, **settings) -> LayaChoiceClassifier:
    return LayaChoiceClassifier(Settings(_env_file=None, **settings), httpx.MockTransport(handler))


def answering(probabilities: dict):
    body = {"answers": {"choice": {"type": "choice", "choice": "x", "probabilities": probabilities}}}
    return lambda request: httpx.Response(200, json=body)


class TestRequest:
    def test_asks_one_choice_question_with_the_text_as_a_named_field(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["url"] = str(request.url)
            seen["body"] = json.loads(request.content)
            return answering({"Sales": 0.7, "Purchase": 0.2, "Other": 0.1})(request)

        classifier_with(handler).choose("sales in august", "Which department should handle this?", CHOICES)
        assert seen["url"] == "http://localhost:8000/v1/systemone"
        assert seen["body"] == {
            "state": {"question": "sales in august"},
            "questions": {"choice": {"type": "choice", "instructions": "Which department should handle this?", "criteria": CHOICES}},
            "model": "typed-decisions",
        }

    def test_the_checkpoint_comes_from_settings(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["model"] = json.loads(request.content)["model"]
            return answering({"Sales": 1, "Purchase": 0, "Other": 0})(request)

        classifier_with(handler, laya_model="english").choose("x", "q", CHOICES)
        assert seen["model"] == "english"

    def test_sends_the_api_key_only_when_there_is_one(self):
        seen = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.headers.get("authorization"))
            return answering({"Sales": 1, "Purchase": 0, "Other": 0})(request)

        classifier_with(handler, laya_api_key="secret").choose("x", "q", CHOICES)
        classifier_with(handler).choose("x", "q", CHOICES)
        assert seen == ["Bearer secret", None]


class TestDecision:
    def test_picks_the_most_likely_choice_with_its_probability(self):
        decision = classifier_with(answering({"Sales": 0.2, "Purchase": 0.65, "Other": 0.15})).choose("x", "q", CHOICES)
        assert decision == Decision("Purchase", 0.65)

    def test_keeps_the_probability_of_every_offered_choice(self):
        decision = classifier_with(answering({"Sales": 0.2, "Purchase": 0.65, "Other": 0.15, "Extra": 0.9})).choose("x", "q", CHOICES)
        assert decision.scores == {"Sales": 0.2, "Purchase": 0.65, "Other": 0.15}

    def test_only_the_offered_choices_count(self):
        decision = classifier_with(answering({"Sales": 0.2, "Purchase": 0.3, "Other": 0.1, "Extra": 0.9})).choose("x", "q", CHOICES)
        assert decision.choice == "Purchase"


class TestUnavailable:
    @pytest.mark.parametrize("status", [401, 422, 500, 503])
    def test_any_other_status_is_unavailable(self, status):
        with pytest.raises(ClassifierUnavailable):
            classifier_with(lambda request: httpx.Response(status)).choose("x", "q", CHOICES)

    @pytest.mark.parametrize("error", [httpx.ConnectError("refused"), httpx.ReadTimeout("slow")])
    def test_a_connection_error_or_timeout_is_unavailable(self, error):
        def handler(request: httpx.Request) -> httpx.Response:
            raise error

        with pytest.raises(ClassifierUnavailable):
            classifier_with(handler).choose("x", "q", CHOICES)

    @pytest.mark.parametrize("body", [{}, {"answers": {}}, {"answers": {"choice": {"probabilities": {}}}}, {"answers": {"choice": {"probabilities": {"Sales": "lots", "Purchase": 0, "Other": 0}}}}, {"answers": {"choice": {"probabilities": {"Sales": 1}}}}])
    def test_an_unreadable_answer_is_unavailable(self, body):
        with pytest.raises(ClassifierUnavailable):
            classifier_with(lambda request: httpx.Response(200, json=body)).choose("x", "q", CHOICES)


class TestSettings:
    def test_defaults_point_at_a_local_laya_with_the_typed_decisions_checkpoint(self):
        settings = Settings(_env_file=None)
        assert (settings.laya_url, settings.laya_model, settings.laya_api_key) == ("http://localhost:8000", "typed-decisions", "")
