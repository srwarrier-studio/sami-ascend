from datetime import date, datetime, timedelta, timezone
from decimal import Decimal

import jwt
import pytest
from fakes import FakeClassifier, FakeMetricSource, FakeUnansweredLog
from fastapi.testclient import TestClient
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from intent_api.application.choose_scenarios import NOTHING, ChooseScenarios
from intent_api.application.match_question import MatchQuestion
from intent_api.application.read_domain import OTHER, ReadDomain
from intent_api.domain.analysis.measure import Comparison as Comparison_, DimensionInfo, MetricInfo, MoverRow, TrendPoint as TrendPoint_
from intent_api.domain.entities.decision import Decision
from intent_api.domain.errors import CompanyNotAllowed
from intent_api.domain.entities.figures import Comparison, MonthFigure, Row, TrendPoint
from intent_api.entrypoint.app import create_app
from intent_api.infrastructure.jsonl_unanswered_log import JsonlUnansweredLog
from intent_api.infrastructure.library_loader import load_library
from intent_api.infrastructure.mock_data_source import MockDataSource
from intent_api.infrastructure.settings import Settings

SECRET = "s" * 32
URL = "/v1/intent/answer"
LIBRARY = load_library()
TODAY = date(2026, 11, 15)
SALES = {"Sales": 0.9, "Purchase": 0.05, "Shipments": 0.02, "Finance": 0.01, "Inventory": 0.01, "Production": 0.01, OTHER: 0.0}
IN_SALES = Decision("Sales", 0.9, SALES)


def token_with(roles: list[str]) -> str:
    payload = {"sub": "user-1", "sap_username": "SAP_USER", "roles": roles, "exp": datetime.now(timezone.utc) + timedelta(minutes=5)}
    return jwt.encode(payload, SECRET, algorithm="HS256")


def comparison(rows=()) -> Comparison:
    return Comparison("INR", Decimal(600), Decimal(500), Decimal(100), Decimal("20.00"), tuple(rows), False)


def customers() -> list[Row]:
    return [Row("C1", "Alder Imports", Decimal(200), Decimal(0)), Row("C2", "Kestrel Logistics", Decimal(400), Decimal(0))]


def trend() -> MonthFigure:
    return MonthFigure("INR", Decimal(600), None, True, (TrendPoint(2026, 5, Decimal(500)), TrendPoint(2026, 6, Decimal(600))))


def client(decisions, source=None, roles=("management",), unanswered_log="/dev/null", analysis=None):
    classifier = FakeClassifier()
    queue = iter(decisions)

    def choose(text, instructions, choices):
        decision = next(queue)
        if isinstance(decision, Exception):
            raise decision
        return decision

    classifier.choose = choose
    log = FakeUnansweredLog()
    matcher = MatchQuestion(ReadDomain(classifier, LIBRARY.domains), ChooseScenarios(classifier, LIBRARY), LIBRARY, 0.0, log)
    source = source or FakeMetricSource(comparisons=[comparison(customers())], months=[trend()])
    app = create_app(Settings(jwt_secret=SECRET, unanswered_log=unanswered_log, _env_file=None), matcher, source, lambda: TODAY, analysis)
    test = TestClient(app)
    if roles is not None:
        test.cookies.set(ACCESS_TOKEN_COOKIE, token_with(list(roles)))
    return test, source


class TestAccess:
    def test_no_cookie_is_401_and_other_roles_are_403(self):
        assert client([], roles=None)[0].post(URL, json={"question": "sales"}).status_code == 401
        assert client([], roles=("sales",))[0].post(URL, json={"question": "sales"}).status_code == 403

    @pytest.mark.parametrize("body", [{}, {"question": ""}, {"question": "x" * 501}])
    def test_a_missing_or_empty_or_long_question_is_422(self, body):
        assert client([])[0].post(URL, json=body).status_code == 422


class TestAnswered:
    def test_a_value_is_a_sentence_and_the_reading_comes_with_it(self):
        test, _ = client([IN_SALES, Decision("sales_value", 0.8)])
        body = test.post(URL, json={"question": "how much did we sell in June"}).json()
        assert (body["problem"], body["reason"], body["periods"]) == (None, None, [])
        assert body["reading"]["domain"] == "Sales"
        assert [item["scenario"] for item in body["answers"]] == ["sales_value"]
        [block] = body["answers"][0]["blocks"]
        assert block == {"type": "text", "lines": ["Sales for June 2026 were INR 600."]}

    def test_a_ranking_is_a_sentence_and_a_table(self):
        test, source = client([IN_SALES, Decision("sales_top_customers", 0.9)])
        body = test.post(URL, json={"question": "to whom did we sell the most in June"}).json()
        blocks = body["answers"][0]["blocks"]
        assert [block["type"] for block in blocks] == ["text", "table"]
        assert blocks[0]["lines"] == ["Kestrel Logistics led sales in June 2026 at INR 400 (66.7% of INR 600)."]
        assert [row["name"] for row in blocks[1]["rows"]] == ["Kestrel Logistics", "Alder Imports"]
        assert source.calls[0][4:] == ("customer", 50)

    def test_the_cookie_of_the_caller_goes_to_the_data_source(self):
        test, source = client([IN_SALES, Decision("sales_value", 0.8)])
        test.post(URL, json={"question": "sales in June"})
        assert source.calls[0][1] == test.cookies[ACCESS_TOKEN_COOKIE]

    def test_a_combined_question_gives_one_answer_per_scenario_in_order(self):
        test, _ = client([IN_SALES, Decision("sales_top_customers", 0.9), Decision("sales_trend", 0.8)])
        body = test.post(URL, json={"question": "top customers in June and the trend"}).json()
        assert [item["scenario"] for item in body["answers"]] == ["sales_top_customers", "sales_trend"]
        assert [block["type"] for block in body["answers"][1]["blocks"]] == ["text", "trend"]

    def test_the_period_is_read_from_the_whole_question(self):
        test, source = client([IN_SALES, Decision("sales_value", 0.8)])
        test.post(URL, json={"question": "sales in March last year"})
        assert source.calls[0][3].start == date(2025, 3, 1)


def without_why(monkeypatch):
    from intent_api.entrypoint import answerer

    real = answerer.load_answers
    monkeypatch.setattr(answerer, "load_answers", lambda library: {k: v for k, v in real(library).items() if k != "sales_why"})


class TestRefused:
    def test_a_question_not_about_the_business_is_refused_as_before(self):
        test, _ = client([Decision(OTHER, 0.9, {**SALES, OTHER: 0.9})])
        body = test.post(URL, json={"question": "tell me a joke"}).json()
        assert (body["problem"], body["reason"], body["answers"]) == ("cannot_answer", "not_about_business", [])
        assert body["reading"]["problem"] == "cannot_answer"

    def test_a_scenario_with_no_answer_is_not_answerable_yet(self, monkeypatch):
        without_why(monkeypatch)
        test, source = client([IN_SALES, Decision("sales_why", 0.9)])
        body = test.post(URL, json={"question": "why did sales fall in June"}).json()
        assert (body["problem"], body["reason"], body["answers"]) == ("cannot_answer", "not_answerable_yet", [])
        assert body["reading"]["scenarios"][0]["id"] == "sales_why"
        assert source.calls == []

    def test_two_periods_are_refused_with_the_periods_named(self):
        test, source = client([IN_SALES, Decision("sales_value", 0.8), Decision("sales_value", 0.8)])
        body = test.post(URL, json={"question": "sales in June and in May"}).json()
        assert (body["problem"], body["reason"], body["periods"]) == ("cannot_answer", "period_not_supported", ["June 2026", "May 2026"])
        assert source.calls == []

    def test_a_period_in_the_future_is_refused(self):
        test, _ = client([IN_SALES, Decision("sales_value", 0.8)])
        assert test.post(URL, json={"question": "sales in 2027"}).json()["periods"] == ["2027"]

    def test_nothing_selected_is_refused_as_before(self):
        test, _ = client([IN_SALES, Decision(NOTHING, 0.9)])
        assert test.post(URL, json={"question": "sales gossip"}).json()["reason"] == "nothing_matched"

    def test_every_refusal_is_logged(self, tmp_path, monkeypatch):
        without_why(monkeypatch)
        path = tmp_path / "unanswered.jsonl"
        test, _ = client([IN_SALES, Decision("sales_why", 0.9)], unanswered_log=path)
        test.post(URL, json={"question": "why did sales fall in June"})
        [entry] = JsonlUnansweredLog(path).entries()
        assert (entry["question"], entry["reason"]) == ("why did sales fall in June", "not_answerable_yet")


class TestOutages:
    def test_synapse_down_is_503_cannot_fetch_now(self):
        source = FakeMetricSource()
        source.down = True
        test, _ = client([IN_SALES, Decision("sales_value", 0.8)], source)
        response = test.post(URL, json={"question": "sales in June"})
        assert (response.status_code, response.json()) == (503, {"problem": "cannot_fetch_now"})

    def test_laya_down_is_503_cannot_classify_now(self):
        from intent_api.domain.errors import ClassifierUnavailable

        test, _ = client([ClassifierUnavailable("down")])
        response = test.post(URL, json={"question": "sales in June"})
        assert (response.status_code, response.json()) == (503, {"problem": "cannot_classify_now"})


class DeniedSource(MockDataSource):
    def compare(self, token, metric, window, by, top):
        raise CompanyNotAllowed(self.companies[-1])


def august_data() -> MockDataSource:
    rows = [MoverRow("A", "Name A", Decimal(100), Decimal(1000), Decimal(-900), Decimal(80))]
    grand = Comparison_("INR", Decimal(900), Decimal(1000), Decimal(-100), Decimal("-10.00"))
    return MockDataSource(
        {"contract": [{"SalesContract": "C-A", "SoldToParty": "A", "ValidFrom": "2026-01-01", "ValidTo": "2027-01-01"}]}, None,
        [MetricInfo("sales", "Sales", (DimensionInfo("customer", False),))],
        {("sales", None): [grand], ("sales", "customer"): [Comparison_("INR", Decimal(900), Decimal(1000), Decimal(-100), Decimal("-10.00"), rows)]},
        {"sales": [TrendPoint_("2026-07", Decimal(1000)), TrendPoint_("2026-08", Decimal(900))]},
    )


class TestWhy:
    def ask(self, question="why did sales fall in August", company=None, analysis=None, source=None):
        test, metrics = client([IN_SALES, Decision("sales_why", 0.9)], source, analysis=analysis or august_data())
        body = {"question": question} if company is None else {"question": question, "company": company}
        return test.post(URL, json=body), metrics

    def test_a_why_question_is_answered_with_the_analysis_blocks(self):
        response, _ = self.ask()
        blocks = response.json()["answers"][0]["blocks"]
        assert response.status_code == 200 and [b["type"] for b in blocks][:2] == ["text", "trend"]
        assert blocks[0]["lines"][0].startswith("Sales of all your companies fell 10.0% in INR from July 2026 to August 2026")

    def test_the_company_scopes_the_analysis(self):
        analysis = august_data()
        response, _ = self.ask(company="sabinsa", analysis=analysis)
        assert analysis.companies == ["sabinsa"]
        assert response.json()["answers"][0]["blocks"][0]["lines"][0].startswith("Sales of Sami-Sabinsa fell")

    def test_a_currency_word_in_the_question_names_the_currency(self):
        response, _ = self.ask("why did sales fall in August in USD")
        assert "no data in USD" in response.json()["answers"][0]["blocks"][0]["lines"][0]

    def test_a_month_not_over_yet_is_one_sentence(self):
        response, _ = self.ask("why did sales fall in November")
        assert response.json()["answers"][0]["blocks"] == [{"type": "text", "lines": ["A why-question needs one finished month, for example August 2026."]}]

    def test_a_company_the_user_does_not_have_is_403(self):
        denied = DeniedSource(infos=[MetricInfo("sales", "Sales", ())])
        response, _ = self.ask(company="organica", analysis=denied)
        assert (response.status_code, response.json()) == (403, {"problem": "company_not_allowed"})

    def test_an_unknown_company_is_422(self):
        assert self.ask(company="acme")[0].status_code == 422

    def test_analysis_down_is_503(self):
        down = august_data()
        down.fail()
        response, _ = self.ask(analysis=down)
        assert (response.status_code, response.json()) == (503, {"problem": "cannot_fetch_now"})


class TestTheCompanyOnTheOtherAnswers:
    def ask(self, company=None):
        test, source = client([IN_SALES, Decision("sales_value", 0.9)])
        body = {"question": "sales in June"} if company is None else {"question": "sales in June", "company": company}
        return test.post(URL, json=body), source

    def test_a_company_is_sent_to_the_metric_reads(self):
        _, source = self.ask("organica")
        assert source.companies == ["organica"]

    def test_all_is_the_default_and_sends_none(self):
        _, source = self.ask()
        assert source.companies == [None]
