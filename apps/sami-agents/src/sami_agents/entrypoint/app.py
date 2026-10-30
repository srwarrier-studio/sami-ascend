from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from structured_logging import RequestIdMiddleware
from token_verification import TokenVerifier
from token_verification.fastapi_deps import AuthDependencies

from sami_agents.application.answer_chat import AnswerChat
from sami_agents.application.keyword_matcher import KeywordMatcher
from sami_agents.application.plan_chat import PlanChat
from sami_agents.domain.errors import CatalogUnavailable
from sami_agents.domain.gateways.catalog_source import CatalogSource
from sami_agents.domain.gateways.chat_model import ChatModel
from sami_agents.infrastructure.alias_book import load_aliases
from sami_agents.infrastructure.api.chat.router import create_chat_router
from sami_agents.infrastructure.api.health.router import create_health_router
from sami_agents.infrastructure.ollama_chat_model import OllamaChatModel
from sami_agents.infrastructure.settings import Settings
from sami_agents.infrastructure.synapse_catalog_source import SynapseCatalogSource


def create_app(
    settings: Settings,
    chat_model: ChatModel | None = None,
    catalog_source: CatalogSource | None = None,
) -> FastAPI:
    auth = AuthDependencies(TokenVerifier(settings.jwt_secret))
    app = FastAPI()

    @app.exception_handler(CatalogUnavailable)
    def catalog_unavailable(request: Request, error: CatalogUnavailable) -> JSONResponse:
        return JSONResponse({"code": "CATALOG_UNAVAILABLE"}, status_code=503)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    app.add_middleware(RequestIdMiddleware)
    answer_chat = AnswerChat(catalog_source or SynapseCatalogSource(settings), PlanChat(chat_model or OllamaChatModel(settings), KeywordMatcher(load_aliases())))
    app.include_router(create_health_router(), prefix="/v1/agents", tags=["Health"])
    app.include_router(create_chat_router(answer_chat, auth), prefix="/v1/agents", tags=["Chat"])
    return app
