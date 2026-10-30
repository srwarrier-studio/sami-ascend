import uvicorn

from sami_agents.entrypoint.app import create_app
from sami_agents.infrastructure.settings import Settings


def main() -> None:
    settings = Settings()
    if not settings.jwt_secret:
        raise SystemExit("JWT_SECRET is not set")
    uvicorn.run(create_app(settings), host="0.0.0.0", port=8005, log_config=None)
