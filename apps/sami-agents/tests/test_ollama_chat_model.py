import json

import httpx
import pytest

from sami_agents.domain.errors import InvalidModelAnswer, ModelUnavailable
from sami_agents.infrastructure.mock_catalog_source import DEFAULT_ENTRIES
from sami_agents.infrastructure.ollama_chat_model import OllamaChatModel
from sami_agents.infrastructure.settings import Settings


def model_with(handler) -> OllamaChatModel:
    return OllamaChatModel(Settings(_env_file=None), httpx.MockTransport(handler))


def answering(content) -> httpx.MockTransport:
    return lambda request: httpx.Response(200, json={"message": {"role": "assistant", "content": content}})


class TestRequest:
    def test_posts_the_model_the_catalog_and_the_message(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["url"] = str(request.url)
            seen["body"] = json.loads(request.content)
            return httpx.Response(200, json={"message": {"content": '{"widgets": ["sales-today"]}'}})

        model_with(handler).pick_widgets("show sales", DEFAULT_ENTRIES)
        body = seen["body"]
        assert seen["url"] == "http://localhost:11434/api/chat"
        assert body["model"] == "gemma3:270m"
        assert body["stream"] is False
        assert body["options"] == {"temperature": 0}
        assert body["messages"][1] == {"role": "user", "content": "show sales"}
        assert "sales-today: Sales today - Net sales invoiced today against yesterday." in body["messages"][0]["content"]

    def test_the_schema_only_allows_catalog_ids(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["format"] = json.loads(request.content)["format"]
            return httpx.Response(200, json={"message": {"content": '{"widgets": []}'}})

        model_with(handler).pick_widgets("hi", DEFAULT_ENTRIES)
        assert seen["format"]["properties"]["widgets"]["items"]["enum"] == [entry.id for entry in DEFAULT_ENTRIES]
        assert seen["format"]["required"] == ["widgets"]

    def test_uses_the_configured_model_and_url(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["url"] = str(request.url)
            seen["model"] = json.loads(request.content)["model"]
            return httpx.Response(200, json={"message": {"content": '{"widgets": []}'}})

        settings = Settings(ollama_url="http://ollama.test:1234", ollama_model="lfm2.5-1.2b", _env_file=None)
        OllamaChatModel(settings, httpx.MockTransport(handler)).pick_widgets("hi", DEFAULT_ENTRIES)
        assert seen == {"url": "http://ollama.test:1234/api/chat", "model": "lfm2.5-1.2b"}


class TestAnswer:
    def test_reads_the_ids(self):
        assert model_with(answering('{"widgets": ["sales-today", "top-customers"]}')).pick_widgets("x", DEFAULT_ENTRIES) == ["sales-today", "top-customers"]

    def test_an_empty_list_is_a_valid_answer(self):
        assert model_with(answering('{"widgets": []}')).pick_widgets("x", DEFAULT_ENTRIES) == []

    @pytest.mark.parametrize("content", ["not json", "{}", '{"widgets": "sales-today"}', '{"widgets": [1, 2]}', '["sales-today"]', "null"])
    def test_an_unreadable_answer_is_invalid(self, content):
        with pytest.raises(InvalidModelAnswer):
            model_with(answering(content)).pick_widgets("x", DEFAULT_ENTRIES)

    def test_a_body_without_a_message_is_invalid(self):
        with pytest.raises(InvalidModelAnswer):
            model_with(lambda request: httpx.Response(200, json={"oops": True})).pick_widgets("x", DEFAULT_ENTRIES)


class TestUnavailable:
    @pytest.mark.parametrize("status", [404, 500, 503])
    def test_any_other_status_is_unavailable(self, status):
        with pytest.raises(ModelUnavailable):
            model_with(lambda request: httpx.Response(status)).pick_widgets("x", DEFAULT_ENTRIES)

    def test_a_connection_error_is_unavailable(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ConnectError("refused")

        with pytest.raises(ModelUnavailable):
            model_with(handler).pick_widgets("x", DEFAULT_ENTRIES)

    def test_a_timeout_is_unavailable(self):
        def handler(request: httpx.Request) -> httpx.Response:
            raise httpx.ReadTimeout("slow")

        with pytest.raises(ModelUnavailable):
            model_with(handler).pick_widgets("x", DEFAULT_ENTRIES)
