from datetime import datetime, timedelta, timezone

import jwt
import pytest
from fakes import FakeClassifier, FakeUnansweredLog
from fastapi.testclient import TestClient
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from intent_api.application.choose_scenarios import NOTHING, ChooseScenarios
from intent_api.application.match_question import MatchQuestion
from intent_api.application.read_domain import OTHER, ReadDomain
from intent_api.domain.entities.decision import Decision
from intent_api.entrypoint.app import create_app
from intent_api.infrastructure.library_loader import load_library
from intent_api.infrastructure.settings import Settings

SECRET = "s" * 32
URL = "/v1/intent/match"
LIBRARY = load_library()
SCORES = {"Sales": 0.9, "Purchase": 0.05, "Shipments": 0.02, "Finance": 0.01, "Inventory": 0.01, "Production": 0.01, OTHER: 0.0}


def token_with(roles: list[str]) -> str:
    payload = {"sub": "user-1", "sap_username": "SAP_USER", "roles": roles, "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    return jwt.encode(payload, SECRET, algorithm="HS256")


def client(answers, roles=None, min_probability=0.0):
    classifier = FakeClassifier()
    queue = iter(answers)

    def choose(text, instructions, choices):
        decision = next(queue)
        if isinstance(decision, Exception):
            raise decision
        return decision

    classifier.choose = choose
    log = FakeUnansweredLog()
    matcher = MatchQuestion(ReadDomain(classifier, LIBRARY.domains), ChooseScenarios(classifier, LIBRARY), LIBRARY, min_probability, log)
    test = TestClient(create_app(Settings(jwt_secret=SECRET, _env_file=None), matcher))
    if roles is not None:
        test.cookies.set(ACCESS_TOKEN_COOKIE, token_with(roles))
    return test, log


ANSWERED = [Decision("Sales", 0.9, SCORES), Decision("sales_value", 0.8)]


class TestAccess:
    def test_no_cookie_is_401_and_other_roles_are_403(self):
        assert client(ANSWERED)[0].post(URL, json={"question": "sales"}).status_code == 401
        assert client(ANSWERED, ["sales"])[0].post(URL, json={"question": "sales"}).status_code == 403

    @pytest.mark.parametrize("roles", [["management"], ["admin"]])
    def test_management_and_admin_pass(self, roles):
        assert client(ANSWERED, roles)[0].post(URL, json={"question": "sales"}).status_code == 200

    @pytest.mark.parametrize("body", [{}, {"question": ""}, {"question": "   "}, {"question": "x" * 501}])
    def test_a_missing_or_empty_or_long_question_is_422(self, body):
        assert client(ANSWERED, ["management"])[0].post(URL, json=body).status_code == 422


class TestAnswered:
    def test_returns_the_domain_the_scenarios_and_what_was_offered(self):
        test, log = client(ANSWERED, ["management"])
        body = test.post(URL, json={"question": " sales in august "}).json()
        assert body["problem"] is None and body["reason"] is None
        assert (body["domain"], body["domain_probability"]) == ("Sales", 0.9)
        assert body["scenarios"] == [{"id": "sales_value", "probability": 0.8, "clause": "sales in august"}]
        assert "sales_why" in body["offered"] and "purchases_value" not in body["offered"]
        assert body["domain_scores"]["Purchase"] == 0.05
        assert log.logged == []


class TestRefused:
    def test_a_question_not_about_the_business_is_cannot_answer_with_two_choices_and_one_log_entry(self):
        test, log = client([Decision(OTHER, 0.6, {**SCORES, "Sales": 0.2, "Purchase": 0.15, OTHER: 0.6})], ["management"])
        response = test.post(URL, json={"question": "tell me a joke"})
        body = response.json()
        assert response.status_code == 200
        assert (body["problem"], body["reason"], body["did_you_mean"], body["scenarios"]) == ("cannot_answer", "not_about_business", ["Sales", "Purchase"], [])
        assert [question for question, _ in log.logged] == ["tell me a joke"]

    def test_a_domain_without_scenarios_names_the_domain(self):
        test, log = client([Decision("Finance", 0.9, {**SCORES, "Finance": 0.9, "Sales": 0.05})], ["management"])
        body = test.post(URL, json={"question": "who owes us money"}).json()
        assert (body["problem"], body["reason"], body["domain"]) == ("cannot_answer", "no_scenarios", "Finance")
        assert len(log.logged) == 1

    def test_nothing_selected_is_cannot_answer(self):
        test, _ = client([Decision("Sales", 0.9, SCORES), Decision(NOTHING, 0.7)], ["management"])
        assert test.post(URL, json={"question": "sales"}).json()["reason"] == "nothing_matched"

    def test_a_domain_below_the_minimum_is_not_sure(self):
        test, _ = client([Decision("Sales", 0.4, {**SCORES, "Sales": 0.4})], ["management"], min_probability=0.5)
        assert test.post(URL, json={"question": "revnue"}).json()["reason"] == "not_sure"


class TestLayaDown:
    def test_is_cannot_classify_now_and_nothing_is_logged(self):
        from intent_api.domain.errors import ClassifierUnavailable

        test, log = client([ClassifierUnavailable("down")], ["management"])
        response = test.post(URL, json={"question": "sales in august"})
        assert (response.status_code, response.json()) == (503, {"problem": "cannot_classify_now"})
        assert log.logged == []
