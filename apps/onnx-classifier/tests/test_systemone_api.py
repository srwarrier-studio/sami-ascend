from fakes import FakePairScorer
from fastapi.testclient import TestClient

from onnx_classifier.application.score_choice import ScoreChoice
from onnx_classifier.entrypoint.app import create_app
from onnx_classifier.infrastructure.settings import Settings

BODY = {
    "state": {"question": "how much did we sell"},
    "questions": {"choice": {"type": "choice", "instructions": "Which?", "criteria": {"Sales": "sales", "Finance": "cash"}}},
    "model": "anything",
}


def client(api_key: str = "") -> TestClient:
    score = ScoreChoice(FakePairScorer([2.0, 0.0]), 1.0)
    return TestClient(create_app(Settings(api_key=api_key), score))


class TestAnswer:
    def test_returns_probabilities_for_exactly_the_offered_options(self):
        response = client().post("/v1/systemone", json=BODY)
        assert response.status_code == 200
        probabilities = response.json()["answers"]["choice"]["probabilities"]
        assert set(probabilities) == {"Sales", "Finance"}
        assert probabilities["Sales"] > probabilities["Finance"]

    def test_the_model_field_is_accepted_and_ignored(self):
        assert client().post("/v1/systemone", json={k: v for k, v in BODY.items() if k != "model"}).status_code == 200


class TestBadRequests:
    def test_a_question_that_is_not_a_choice_is_refused(self):
        body = {**BODY, "questions": {"choice": {"type": "score", "criteria": {"a": "b"}}}}
        assert client().post("/v1/systemone", json=body).status_code == 422

    def test_a_choice_with_no_options_is_refused(self):
        body = {**BODY, "questions": {"choice": {"type": "choice", "instructions": "x", "criteria": {}}}}
        assert client().post("/v1/systemone", json=body).status_code == 422

    def test_a_state_without_the_question_text_is_refused(self):
        assert client().post("/v1/systemone", json={**BODY, "state": {"other": "x"}}).status_code == 422


class TestApiKey:
    def test_no_key_configured_means_open(self):
        assert client().post("/v1/systemone", json=BODY).status_code == 200

    def test_a_configured_key_is_required(self):
        assert client("secret").post("/v1/systemone", json=BODY).status_code == 401

    def test_a_wrong_key_is_refused_and_the_right_key_works(self):
        app = client("secret")
        assert app.post("/v1/systemone", json=BODY, headers={"Authorization": "Bearer nope"}).status_code == 401
        assert app.post("/v1/systemone", json=BODY, headers={"Authorization": "Bearer secret"}).status_code == 200


class TestHealth:
    def test_health_answers_without_a_key(self):
        assert client("secret").get("/health").json() == {"status": "ok"}
