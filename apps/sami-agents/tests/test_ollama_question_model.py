import json

import httpx

from sami_agents.infrastructure.ollama_question_model import OllamaHeadlineRewriter, OllamaQuestionModel
from sami_agents.infrastructure.settings import Settings

SETTINGS = Settings(ollama_url="http://ollama", ollama_model="tiny", _env_file=None)


def transport(content=None, status=200, error=None, seen=None):
    def handler(request):
        if seen is not None:
            seen.append(json.loads(request.content))
        if error:
            raise error
        return httpx.Response(status, json={"message": {"content": content}})

    return httpx.MockTransport(handler)


class TestTheQuestionModel:
    def test_it_asks_for_json_with_the_registered_metrics_and_returns_the_parsed_answer(self):
        seen = []
        model = OllamaQuestionModel(SETTINGS, transport('{"metric": "sales", "direction": "fall", "month": "2026-08"}', seen=seen))
        assert model.read("what happened to the money", ["sales", "purchases"]) == {"metric": "sales", "direction": "fall", "month": "2026-08"}
        body = seen[0]
        assert (body["model"], body["format"], body["options"]["temperature"], body["stream"]) == ("tiny", "json", 0, False)
        assert "sales, purchases" in body["messages"][0]["content"] and body["messages"][1]["content"] == "what happened to the money"

    def test_anything_unusable_is_none_and_never_an_error(self):
        for tp in (transport("not json"), transport('["a"]'), transport("{}", status=500), transport(error=httpx.ConnectError("down"))):
            assert OllamaQuestionModel(SETTINGS, tp).read("x", ["sales"]) in (None, {})

    def test_a_list_answer_is_none(self):
        assert OllamaQuestionModel(SETTINGS, transport('["a"]')).read("x", ["sales"]) is None


class TestTheRewriter:
    def test_it_returns_the_text_and_tells_the_model_to_keep_every_figure(self):
        seen = []
        rewriter = OllamaHeadlineRewriter(SETTINGS, transport("Sales dropped.", seen=seen))
        assert rewriter.rewrite("Sales fell 14.4%.") == "Sales dropped."
        assert "Keep every number, date and name" in seen[0]["messages"][0]["content"] and "format" not in seen[0]

    def test_a_failure_is_none(self):
        assert OllamaHeadlineRewriter(SETTINGS, transport(error=httpx.ReadTimeout("slow"))).rewrite("x") is None
        assert OllamaHeadlineRewriter(SETTINGS, transport("x", status=503)).rewrite("x") is None
