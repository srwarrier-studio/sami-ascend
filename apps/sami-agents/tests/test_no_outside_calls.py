import os
import re
from pathlib import Path

import httpx
import pytest

from sami_agents.entrypoint.analyst import build_analyst
from sami_agents.entrypoint.run import turn_tracing_off
from sami_agents.infrastructure.settings import Settings

SOURCE = Path(__file__).resolve().parents[1] / "src" / "sami_agents"
ALLOWED_HTTP_FILES = {
    "infrastructure/synapse_data_source.py", "infrastructure/synapse_catalog_source.py",
    "infrastructure/ollama_question_model.py", "infrastructure/ollama_reply_writer.py", "infrastructure/laya_relevance_checker.py",
    "infrastructure/in_process_stack.py",
}


class TestTracingIsOff:
    def test_the_start_turns_tracing_off_even_when_the_environment_asks_for_it(self, monkeypatch):
        monkeypatch.setenv("LANGSMITH_TRACING", "true")
        monkeypatch.setenv("LANGCHAIN_TRACING_V2", "true")
        turn_tracing_off()
        assert (os.environ["LANGSMITH_TRACING"], os.environ["LANGCHAIN_TRACING_V2"]) == ("false", "false")

    def test_the_tracing_library_agrees_when_it_is_installed(self, monkeypatch):
        utils = pytest.importorskip("langsmith.utils")
        monkeypatch.setenv("LANGSMITH_TRACING", "true")
        turn_tracing_off()
        if hasattr(utils.tracing_is_enabled, "cache_clear"):
            utils.tracing_is_enabled.cache_clear()
        assert utils.tracing_is_enabled() is False


class TestOnlyTheConfiguredServicesAreCalled:
    def clients_built(self, monkeypatch, settings):
        bases = []
        real = httpx.Client.__init__

        def spy(self, *args, **kwargs):
            bases.append(str(kwargs.get("base_url", "")))
            real(self, *args, **kwargs)

        monkeypatch.setattr(httpx.Client, "__init__", spy)
        build_analyst(settings)
        return bases

    def test_without_a_model_the_analyst_talks_to_synapse_api_only(self, monkeypatch):
        bases = self.clients_built(monkeypatch, Settings(synapse_url="http://synapse:8004", ollama_model="", _env_file=None))
        assert set(bases) == {"http://synapse:8004"}

    def test_with_a_model_it_talks_to_synapse_api_and_the_local_ollama_only(self, monkeypatch):
        bases = self.clients_built(monkeypatch, Settings(synapse_url="http://synapse:8004", ollama_url="http://localhost:11434", ollama_model="tiny", _env_file=None))
        assert set(bases) == {"http://synapse:8004", "http://localhost:11434"}

    def test_no_other_file_makes_http_calls(self):
        users = {str(p.relative_to(SOURCE)) for p in SOURCE.rglob("*.py") if re.search(r"httpx\.(Client|AsyncClient|get|post)\b|requests\.|urllib", p.read_text())}
        assert users <= ALLOWED_HTTP_FILES, users - ALLOWED_HTTP_FILES

    def test_the_analyst_code_never_names_a_hosted_model_service(self):
        text = " ".join(p.read_text() for p in SOURCE.rglob("*.py")).lower()
        for name in ("openai.com", "anthropic.com", "api.cohere", "generativelanguage.googleapis"):
            assert name not in text
