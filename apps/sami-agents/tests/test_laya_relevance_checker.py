import json

import httpx
import pytest

from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.domain.errors import RelevanceUnavailable
from sami_agents.entrypoint.run import build_checker
from sami_agents.infrastructure.laya_relevance_checker import LayaRelevanceChecker
from sami_agents.infrastructure.settings import Settings

ENTRY = CatalogEntry("top-customers", "Top customers", "Customers ranked by net sales this month.")


def checker_with(handler, **settings) -> LayaRelevanceChecker:
    return LayaRelevanceChecker(Settings(_env_file=None, **{"laya_url": "http://localhost:8000", **settings}), httpx.MockTransport(handler))


def answering(yes: float):
    body = {"answers": {"fit": {"type": "choice", "choice": "yes", "probabilities": {"yes": yes, "no": 1 - yes}}}}
    return lambda request: httpx.Response(200, json=body)


class TestRequest:
    def test_asks_the_typed_decisions_checkpoint_one_yes_or_no_question(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["url"] = str(request.url)
            seen["body"] = json.loads(request.content)
            return answering(0.7)(request)

        checker_with(handler).check("who are our best customers?", ENTRY)
        body = seen["body"]
        assert seen["url"] == "http://localhost:8000/v1/systemone"
        assert body["model"] == "typed-decisions"
        assert body["state"] == {"request": "who are our best customers?", "widget": "Top customers - Customers ranked by net sales this month."}
        assert body["questions"]["fit"]["type"] == "choice"
        assert list(body["questions"]["fit"]["criteria"]) == ["yes", "no"]

    def test_sends_the_api_key_when_there_is_one(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["auth"] = request.headers.get("authorization")
            return answering(0.7)(request)

        checker_with(handler, laya_api_key="secret").check("x", ENTRY)
        assert seen["auth"] == "Bearer secret"

    def test_sends_no_authorization_without_a_key(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["auth"] = request.headers.get("authorization")
            return answering(0.7)(request)

        checker_with(handler).check("x", ENTRY)
        assert seen["auth"] is None

    def test_uses_the_configured_url(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["url"] = str(request.url)
            return answering(0.7)(request)

        checker_with(handler, laya_url="http://laya.test:9").check("x", ENTRY)
        assert seen["url"] == "http://laya.test:9/v1/systemone"


class TestAnswer:
    @pytest.mark.parametrize("yes", [0.0, 0.0694, 0.35, 0.6626, 1.0])
    def test_returns_the_probability_of_yes(self, yes):
        assert checker_with(answering(yes)).check("x", ENTRY) == yes


class TestUnavailable:
    @pytest.mark.parametrize("status", [401, 422, 500, 503])
    def test_any_other_status_is_unavailable(self, status):
        with pytest.raises(RelevanceUnavailable):
            checker_with(lambda request: httpx.Response(status)).check("x", ENTRY)

    @pytest.mark.parametrize("error", [httpx.ConnectError("refused"), httpx.ReadTimeout("slow")])
    def test_a_connection_error_or_timeout_is_unavailable(self, error):
        def handler(request: httpx.Request) -> httpx.Response:
            raise error

        with pytest.raises(RelevanceUnavailable):
            checker_with(handler).check("x", ENTRY)

    @pytest.mark.parametrize("body", [{}, {"answers": {}}, {"answers": {"fit": {"probabilities": {}}}}, {"answers": {"fit": {"probabilities": {"yes": "lots"}}}}])
    def test_an_unreadable_answer_is_unavailable(self, body):
        with pytest.raises(RelevanceUnavailable):
            checker_with(lambda request: httpx.Response(200, json=body)).check("x", ENTRY)


class TestSettings:
    def test_defaults(self):
        settings = Settings(_env_file=None)
        assert (settings.laya_url, settings.laya_api_key, settings.laya_threshold, settings.laya_timeout_seconds) == ("", "", 0.35, 5.0)

    def test_the_environment_overrides_them(self, monkeypatch):
        monkeypatch.setenv("LAYA_THRESHOLD", "0.5")
        monkeypatch.setenv("LAYA_API_KEY", "k")
        settings = Settings(_env_file=None)
        assert settings.laya_threshold == 0.5 and settings.laya_api_key == "k"

    def test_a_blank_laya_url_turns_the_check_off(self):
        assert build_checker(Settings(_env_file=None, laya_url="")) is None

    def test_a_laya_url_builds_the_checker(self):
        assert isinstance(build_checker(Settings(_env_file=None, laya_url="http://localhost:8000")), LayaRelevanceChecker)

    def test_the_check_is_off_unless_laya_is_configured(self):
        assert build_checker(Settings(_env_file=None)) is None


class TestBuilders:
    def test_the_sentence_writer_is_off_unless_a_model_is_named(self):
        from sami_agents.entrypoint.run import build_reply_writer
        from sami_agents.infrastructure.ollama_reply_writer import OllamaReplyWriter

        assert build_reply_writer(Settings(_env_file=None)) is None
        assert isinstance(build_reply_writer(Settings(_env_file=None, ollama_model="lfm2.5-1.2b")), OllamaReplyWriter)
