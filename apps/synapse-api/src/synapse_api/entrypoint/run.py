import uvicorn

from synapse_api.entrypoint.app import create_app
from synapse_api.infrastructure.butterfly_sales_source import ButterflySalesSource
from synapse_api.infrastructure.settings import Settings


def main() -> None:
    settings = Settings()
    if not settings.jwt_secret:
        raise SystemExit("JWT_SECRET is not set")
    app = create_app(ButterflySalesSource(settings), settings)
    uvicorn.run(app, host="0.0.0.0", port=8004, log_config=None)
