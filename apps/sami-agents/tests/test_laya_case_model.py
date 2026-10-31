import json

import httpx
import pytest

from sami_agents.domain.entities.case import Decision
from sami_agents.domain.errors import CaseModelUnavailable
from sami_agents.infrastructure.laya_case_model import LayaCaseModel
from sami_agents.infrastructure.mock_case_model import MockCaseModel
from sami_agents.infrastructure.settings import Settings

CHOICES = {"why": "an explanation of a change", "figure": "the value of a figure", "other": "something unrelated"}


def model_with(handler, **settings) -> LayaCaseModel:
    return LayaCaseModel(Settings(_env_file=None, **{"laya_url": "http://localhost:8000", **settings}), httpx.MockTransport(handler))


def answering(probabilities: dict, name="intent"):
    body = {"answers": {name: {"type": "choice", "choice": "x", "probabilities": probabilities}}}
    return lambda request: httpx.Response(200, json=body)


class TestRequest:
    def test_asks_one_choice_question_named_for_the_pass(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["url"] = str(request.url)
            seen["body"] = json.loads(request.content)
            return answering({"why": 0.7, "figure": 0.2, "other": 0.1})(request)

        model_with(handler).decide("why did sales drop", "intent", "What does the manager want?", CHOICES)
        body = seen["body"]
        assert seen["url"] == "http://localhost:8000/v1/systemone"
        assert body["model"] == "typed-decisions"
        assert body["state"] == {"request": "why did sales drop"}
        assert body["questions"] == {"intent": {"type": "choice", "instructions": "What does the manager want?", "criteria": CHOICES}}

    def test_sends_the_api_key_only_when_there_is_one(self):
        seen = []

        def handler(request: httpx.Request) -> httpx.Response:
            seen.append(request.headers.get("authorization"))
            return answering({"why": 1, "figure": 0, "other": 0})(request)

        model_with(handler, laya_api_key="secret").decide("x", "intent", "q", CHOICES)
        model_with(handler).decide("x", "intent", "q", CHOICES)
        assert seen == ["Bearer secret", None]


class TestDecision:
    def test_picks_the_most_likely_choice_with_its_probability(self):
        decision = model_with(answering({"why": 0.2, "figure": 0.65, "other": 0.15})).decide("x", "intent", "q", CHOICES)
        assert decision == Decision("figure", 0.65)

    def test_only_the_offered_choices_count(self):
        decision = model_with(answering({"why": 0.2, "figure": 0.3, "other": 0.1, "extra": 0.9})).decide("x", "intent", "q", CHOICES)
        assert decision.choice == "figure"


class TestUnavailable:
    @pytest.mark.parametrize("status", [401, 422, 500, 503])
    def test_any_other_status_is_unavailable(self, status):
        with pytest.raises(CaseModelUnavailable):
            model_with(lambda request: httpx.Response(status)).decide("x", "intent", "q", CHOICES)

    @pytest.mark.parametrize("error", [httpx.ConnectError("refused"), httpx.ReadTimeout("slow")])
    def test_a_connection_error_or_timeout_is_unavailable(self, error):
        def handler(request: httpx.Request) -> httpx.Response:
            raise error

        with pytest.raises(CaseModelUnavailable):
            model_with(handler).decide("x", "intent", "q", CHOICES)

    @pytest.mark.parametrize("body", [{}, {"answers": {}}, {"answers": {"intent": {"probabilities": {}}}}, {"answers": {"intent": {"probabilities": {"why": "lots", "figure": 0, "other": 0}}}}, {"answers": {"intent": {"probabilities": {"why": 1}}}}])
    def test_an_unreadable_answer_is_unavailable(self, body):
        with pytest.raises(CaseModelUnavailable):
            model_with(lambda request: httpx.Response(200, json=body)).decide("x", "intent", "q", CHOICES)

    def test_a_body_that_is_not_json_is_unavailable(self):
        with pytest.raises(CaseModelUnavailable):
            model_with(lambda request: httpx.Response(200, content=b"nope")).decide("x", "intent", "q", CHOICES)


class TestMockCaseModel:
    def test_returns_the_scripted_decision_and_records_the_call(self):
        mock = MockCaseModel({"intent": ("why", 0.8)})
        assert mock.decide("why?", "intent", "q", CHOICES) == Decision("why", 0.8)
        assert mock.calls == [("intent", "why?")]

    def test_an_unscripted_pass_or_a_failing_mock_is_unavailable(self):
        with pytest.raises(CaseModelUnavailable):
            MockCaseModel().decide("x", "subject", "q", CHOICES)
        with pytest.raises(CaseModelUnavailable):
            MockCaseModel({"intent": ("why", 1)}, failing=True).decide("x", "intent", "q", CHOICES)


class TestSettings:
    def test_the_pass_confidence_defaults_to_half_and_can_be_set(self, monkeypatch):
        assert Settings(_env_file=None).pass_min_confidence == 0.5
        monkeypatch.setenv("PASS_MIN_CONFIDENCE", "0.6")
        assert Settings(_env_file=None).pass_min_confidence == 0.6
