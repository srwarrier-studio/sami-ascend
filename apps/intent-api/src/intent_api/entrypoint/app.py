from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from structured_logging import RequestIdMiddleware
from token_verification import TokenVerifier
from token_verification.fastapi_deps import AuthDependencies

from intent_api.application.match_question import MatchQuestion
from intent_api.domain.errors import ClassifierUnavailable
from intent_api.entrypoint.matcher import build_matcher
from intent_api.infrastructure.api.health.router import create_health_router
from intent_api.infrastructure.api.match.router import create_match_router
from intent_api.infrastructure.settings import Settings


def create_app(settings: Settings, matcher: MatchQuestion | None = None) -> FastAPI:
    auth = AuthDependencies(TokenVerifier(settings.jwt_secret))
    app = FastAPI()

    @app.exception_handler(ClassifierUnavailable)
    def classifier_unavailable(request: Request, error: ClassifierUnavailable) -> JSONResponse:
        return JSONResponse({"problem": "cannot_classify_now"}, status_code=503)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    app.add_middleware(RequestIdMiddleware)
    app.include_router(create_health_router(), prefix="/v1/intent", tags=["Health"])
    app.include_router(create_match_router(matcher or build_matcher(settings), auth), prefix="/v1/intent", tags=["Match"])
    return app
