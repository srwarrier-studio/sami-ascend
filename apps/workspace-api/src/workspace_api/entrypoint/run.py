import uvicorn

from workspace_api.application.order_worker import OrderWorker
from workspace_api.application.throttled_gateway import ThrottledGateway
from workspace_api.entrypoint.app import create_app
from workspace_api.entrypoint.workers import start_workers
from workspace_api.infrastructure.butterfly_purchase_requisition_gateway import ButterflyPurchaseRequisitionGateway
from workspace_api.infrastructure.butterfly_sales_order_gateway import ButterflySalesOrderGateway
from workspace_api.infrastructure.settings import Settings
from workspace_api.infrastructure.sqlite_order_request_store import SqliteOrderRequestStore


def main() -> None:
    settings = Settings()
    if not settings.jwt_secret:
        raise SystemExit("JWT_SECRET is not set")
    gateway = ThrottledGateway(ButterflySalesOrderGateway(settings), settings.sap_write_limit, settings.sap_write_wait_seconds)
    store = SqliteOrderRequestStore(settings.order_db)
    store.recover_sending()
    start_workers(OrderWorker(store, gateway, settings.order_max_attempts), settings.order_workers)
    uvicorn.run(create_app(gateway, settings, store, ButterflyPurchaseRequisitionGateway(settings)), host="0.0.0.0", port=8002, log_config=None)
