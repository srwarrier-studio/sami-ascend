from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from structured_logging import RequestIdMiddleware

from intent_api.infrastructure.api.health.router import create_health_router
from intent_api.infrastructure.settings import Settings


def create_app(settings: Settings) -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.frontend_url],
        allow_methods=["*"],
        allow_headers=["*"],
        allow_credentials=True,
    )
    app.add_middleware(RequestIdMiddleware)
    app.include_router(create_health_router(), prefix="/v1/intent", tags=["Health"])
    return app
