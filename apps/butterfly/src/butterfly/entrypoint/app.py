import logging
from datetime import date

import uvicorn
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import JSONResponse
from structured_logging import RequestIdMiddleware, get_request_id, setup_logging

from butterfly.application.usecase.get_sales_order import GetSalesOrder
from butterfly.application.usecase.list_sales_orders import ListSalesOrders
from butterfly.domain.errors import SalesOrderNotFound
from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo
from butterfly.infrastructure.api.odata import ROOT, error_body, etag, order_to_json
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo
from butterfly.infrastructure.memory.seed import build_seed

logger = logging.getLogger("butterfly")


def create_app(repo: SalesOrderRepo) -> FastAPI:
    app = FastAPI()
    router = APIRouter(prefix=ROOT.rstrip("/"))

    @router.get("/SalesOrder")
    def list_orders():
        orders = ListSalesOrders(repo).execute()
        return {
            "@odata.context": "$metadata#SalesOrder",
            "value": [order_to_json(order) for order in orders],
        }

    @router.get("/SalesOrder('{key}')")
    def get_order(key: str):
        order = GetSalesOrder(repo).execute(key)
        return JSONResponse(
            {"@odata.context": "$metadata#SalesOrder/$entity", "@odata.etag": etag(order)}
            | order_to_json(order)
        )

    @app.exception_handler(SalesOrderNotFound)
    def not_found(request: Request, error: SalesOrderNotFound):
        return JSONResponse(
            error_body(
                "SALES_ORDER_NOT_FOUND",
                f"Sales order {error.sales_order} does not exist.",
                "SalesOrder",
            ),
            status_code=404,
        )

    @app.middleware("http")
    async def internal_error(request: Request, call_next):
        try:
            return await call_next(request)
        except Exception:
            logger.exception("Unhandled error")
            return JSONResponse(
                error_body(
                    "INTERNAL_ERROR",
                    "An unexpected error occurred. Quote the request id when reporting it.",
                    get_request_id(),
                ),
                status_code=500,
            )

    app.add_middleware(RequestIdMiddleware)
    app.include_router(router)
    return app


setup_logging("butterfly")
app = create_app(InMemorySalesOrderRepo(build_seed(date.today())))


def main():
    uvicorn.run(app, host="0.0.0.0", port=8003, log_config=None)


if __name__ == "__main__":
    main()
