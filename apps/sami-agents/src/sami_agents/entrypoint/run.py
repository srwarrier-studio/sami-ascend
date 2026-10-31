import os

import uvicorn

from sami_agents.domain.gateways.relevance_checker import RelevanceChecker
from sami_agents.domain.gateways.reply_writer import ReplyWriter
from sami_agents.entrypoint.app import create_app
from sami_agents.infrastructure.laya_relevance_checker import LayaRelevanceChecker
from sami_agents.infrastructure.ollama_reply_writer import OllamaReplyWriter
from sami_agents.infrastructure.settings import Settings


def turn_tracing_off() -> None:
    os.environ["LANGSMITH_TRACING"] = "false"
    os.environ["LANGCHAIN_TRACING_V2"] = "false"


def build_checker(settings: Settings) -> RelevanceChecker | None:
    return LayaRelevanceChecker(settings) if settings.laya_url else None


def build_reply_writer(settings: Settings) -> ReplyWriter | None:
    return OllamaReplyWriter(settings) if settings.ollama_model else None


def main() -> None:
    turn_tracing_off()
    settings = Settings()
    if not settings.jwt_secret:
        raise SystemExit("JWT_SECRET is not set")
    uvicorn.run(create_app(settings, build_checker(settings), reply_writer=build_reply_writer(settings)), host="0.0.0.0", port=8005, log_config=None)
