import uvicorn

from intent_api.entrypoint.app import create_app
from intent_api.infrastructure.settings import Settings


def main() -> None:
    settings = Settings()
    if not settings.jwt_secret:
        raise SystemExit("JWT_SECRET is not set")
    uvicorn.run(create_app(settings), host="0.0.0.0", port=8006, log_config=None)
