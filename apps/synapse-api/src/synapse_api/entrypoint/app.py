from collections.abc import Callable
from datetime import date

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from structured_logging import RequestIdMiddleware
from token_verification import TokenVerifier
from token_verification.fastapi_deps import AuthDependencies

from synapse_api.domain.errors import InvalidQuery, SapUnavailable
from synapse_api.domain.gateways.sales_source import SalesSource
from synapse_api.infrastructure.api.sales.router import create_sales_router
from synapse_api.infrastructure.settings import Settings


def create_app(source: SalesSource, settings: Settings, today: Callable[[], date] = date.today) -> FastAPI:
    auth = AuthDependencies(TokenVerifier(settings.jwt_secret))
    app = FastAPI()

    @app.exception_handler(InvalidQuery)
    def invalid_query(request: Request, error: InvalidQuery) -> JSONResponse:
        return JSONResponse({"code": "INVALID_QUERY", "message": str(error)}, status_code=422)

    @app.exception_handler(SapUnavailable)
    def unavailable(request: Request, error: SapUnavailable) -> JSONResponse:
        return JSONResponse({"code": "SAP_UNAVAILABLE"}, status_code=503)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    app.add_middleware(RequestIdMiddleware)
    app.include_router(create_sales_router(source, auth, today), prefix="/v1/synapse", tags=["Sales"])
    return app
