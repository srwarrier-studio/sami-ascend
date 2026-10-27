import uvicorn

from workspace_api.entrypoint.app import create_app
from workspace_api.infrastructure.butterfly_sales_order_gateway import ButterflySalesOrderGateway
from workspace_api.infrastructure.settings import Settings


def main() -> None:
    settings = Settings()
    if not settings.jwt_secret:
        raise SystemExit("JWT_SECRET is not set")
    app = create_app(ButterflySalesOrderGateway(settings), settings)
    uvicorn.run(app, host="0.0.0.0", port=8002, log_config=None)
