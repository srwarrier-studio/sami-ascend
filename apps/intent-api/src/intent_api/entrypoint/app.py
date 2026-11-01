from datetime import date

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from structured_logging import RequestIdMiddleware
from token_verification import TokenVerifier
from token_verification.fastapi_deps import AuthDependencies

from intent_api.application.match_question import MatchQuestion
from intent_api.domain.analysis.data_source import DataSource
from intent_api.domain.errors import ClassifierUnavailable, CompanyNotAllowed, MetricsUnavailable
from intent_api.domain.gateways.metric_source import MetricSource
from intent_api.entrypoint.answerer import build_answerer
from intent_api.entrypoint.matcher import build_matcher
from intent_api.infrastructure.api.answer.router import create_answer_router
from intent_api.infrastructure.api.health.router import create_health_router
from intent_api.infrastructure.api.match.router import create_match_router
from intent_api.infrastructure.settings import Settings


def create_app(settings: Settings, matcher: MatchQuestion | None = None, metrics: MetricSource | None = None, today=date.today, analysis: DataSource | None = None) -> FastAPI:
    auth = AuthDependencies(TokenVerifier(settings.jwt_secret))
    app = FastAPI()

    @app.exception_handler(ClassifierUnavailable)
    def classifier_unavailable(request: Request, error: ClassifierUnavailable) -> JSONResponse:
        return JSONResponse({"problem": "cannot_classify_now"}, status_code=503)

    @app.exception_handler(CompanyNotAllowed)
    def company_not_allowed(request: Request, error: CompanyNotAllowed) -> JSONResponse:
        return JSONResponse({"problem": "company_not_allowed"}, status_code=403)

    @app.exception_handler(MetricsUnavailable)
    def metrics_unavailable(request: Request, error: MetricsUnavailable) -> JSONResponse:
        return JSONResponse({"problem": "cannot_fetch_now"}, status_code=503)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    app.add_middleware(RequestIdMiddleware)
    app.include_router(create_health_router(), prefix="/v1/intent", tags=["Health"])
    matcher = matcher or build_matcher(settings)
    app.include_router(create_match_router(matcher, auth), prefix="/v1/intent", tags=["Match"])
    app.include_router(create_answer_router(build_answerer(settings, matcher, metrics, analysis), auth, today), prefix="/v1/intent", tags=["Answer"])
    return app
