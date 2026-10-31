import json

import httpx
import pytest

from sami_agents.domain.errors import ReplyUnavailable
from sami_agents.infrastructure.ollama_reply_writer import OllamaReplyWriter
from sami_agents.infrastructure.settings import Settings


def writer_with(handler, **settings) -> OllamaReplyWriter:
    return OllamaReplyWriter(Settings(_env_file=None, **{"ollama_model": "lfm2.5-1.2b", **settings}), httpx.MockTransport(handler))


def answering(content):
    return lambda request: httpx.Response(200, json={"message": {"role": "assistant", "content": content}})


class TestRequest:
    def test_asks_the_configured_model_for_a_short_sentence_about_the_titles(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["url"] = str(request.url)
            seen["body"] = json.loads(request.content)
            return answering("Showing the top customers.")(request)

        writer_with(handler).write("best customers", ["Top customers", "Top materials"], None)
        body = seen["body"]
        assert seen["url"] == "http://localhost:11434/api/chat"
        assert body["model"] == "lfm2.5-1.2b" and body["stream"] is False
        assert body["options"] == {"temperature": 0, "num_predict": 60}
        assert body["messages"][1]["content"] == "Request: best customers\nThese widgets: Top customers, Top materials"
        assert "one short" in body["messages"][0]["content"] and "Do not use numbers" in body["messages"][0]["content"]

    def test_a_board_is_named_in_the_request(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["user"] = json.loads(request.content)["messages"][1]["content"]
            return answering("Done for you now.")(request)

        writer_with(handler).write("finance", ["Receivables outstanding"], "Finance")
        assert seen["user"] == "Request: finance\nA board called Finance with these widgets: Receivables outstanding"

    def test_uses_the_configured_url(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["url"] = str(request.url)
            return answering("Showing it now for you.")(request)

        writer_with(handler, ollama_url="http://ollama.test:1234").write("x", ["T"], None)
        assert seen["url"] == "http://ollama.test:1234/api/chat"


class TestAnswer:
    def test_returns_the_text_the_model_wrote(self):
        assert writer_with(answering("Showing the top customers.")).write("x", ["Top customers"], None) == "Showing the top customers."


class TestUnavailable:
    @pytest.mark.parametrize("status", [404, 500, 503])
    def test_any_other_status_is_unavailable(self, status):
        with pytest.raises(ReplyUnavailable):
            writer_with(lambda request: httpx.Response(status)).write("x", ["T"], None)

    @pytest.mark.parametrize("error", [httpx.ConnectError("refused"), httpx.ReadTimeout("slow")])
    def test_a_connection_error_or_timeout_is_unavailable(self, error):
        def handler(request: httpx.Request) -> httpx.Response:
            raise error

        with pytest.raises(ReplyUnavailable):
            writer_with(handler).write("x", ["T"], None)

    @pytest.mark.parametrize("body", [{}, {"message": {}}, {"message": "text"}])
    def test_an_unreadable_body_is_unavailable(self, body):
        with pytest.raises(ReplyUnavailable):
            writer_with(lambda request: httpx.Response(200, json=body)).write("x", ["T"], None)
