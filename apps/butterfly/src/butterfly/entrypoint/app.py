import logging
from datetime import date

import uvicorn
from fastapi import APIRouter, FastAPI, Query, Request
from fastapi.responses import JSONResponse
from structured_logging import RequestIdMiddleware, get_request_id, setup_logging

from butterfly.application.dto.list_query_dto import ListQuery
from butterfly.application.filter.fields import SALES_ORDER_FIELDS, SALES_ORDER_ITEM_FIELDS
from butterfly.application.query_options import parse_expand
from butterfly.application.usecase.get_sales_order import GetSalesOrder
from butterfly.application.usecase.list_sales_order_items import ListSalesOrderItems
from butterfly.application.usecase.list_sales_orders import ListSalesOrders
from butterfly.domain.errors import InvalidQuery, SalesOrderNotFound, UnsupportedQueryOption
from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo
from butterfly.infrastructure.api.odata import (
    ROOT,
    error_body,
    etag,
    item_to_json,
    order_to_json,
)
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo
from butterfly.infrastructure.memory.seed import build_seed

logger = logging.getLogger("butterfly")

LIST_OPTIONS = {"$filter", "$select", "$orderby", "$top", "$skip", "$count"}
ORDER_LIST_OPTIONS = LIST_OPTIONS | {"$expand"}
SINGLE_ORDER_OPTIONS = {"$expand"}


def reject_unsupported(request: Request, supported: set[str]):
    for name in request.query_params:
        if name.startswith("$") and name not in supported:
            raise UnsupportedQueryOption(f"Query option {name} is not supported.", name)


def context_for(entity: str, select: list[str], fields: dict, expand: bool) -> str:
    parts = [] if select == list(fields) else list(select)
    if expand:
        parts.append("_Item()")
    return "$metadata#" + entity + ("(" + ",".join(parts) + ")" if parts else "")


def order_row(order, select: list[str] | None, expand: bool) -> dict:
    row = order_to_json(order, select)
    if expand:
        row["_Item"] = [item_to_json(item) for item in order.items]
    return row


def create_app(repo: SalesOrderRepo) -> FastAPI:
    app = FastAPI()
    router = APIRouter(prefix=ROOT.rstrip("/"))

    @router.get("/SalesOrder")
    def list_orders(
        request: Request,
        filter_text: str | None = Query(None, alias="$filter"),
        select: str | None = Query(None, alias="$select"),
        orderby: str | None = Query(None, alias="$orderby"),
        top: str | None = Query(None, alias="$top"),
        skip: str | None = Query(None, alias="$skip"),
        count: str | None = Query(None, alias="$count"),
        expand: str | None = Query(None, alias="$expand"),
    ):
        reject_unsupported(request, ORDER_LIST_OPTIONS)
        query = ListQuery(filter_text, select, orderby, top, skip, count)
        result = ListSalesOrders(repo).execute(query, expand)
        body = {"@odata.context": context_for("SalesOrder", result.select, SALES_ORDER_FIELDS, result.expand)}
        if result.total is not None:
            body["@odata.count"] = result.total
        body["value"] = [order_row(order, result.select, result.expand) for order in result.rows]
        return body

    @router.get("/SalesOrder('{key}')")
    def get_order(
        key: str, request: Request, expand: str | None = Query(None, alias="$expand")
    ):
        reject_unsupported(request, SINGLE_ORDER_OPTIONS)
        expanded = parse_expand(expand)
        order = GetSalesOrder(repo).execute(key)
        context = context_for("SalesOrder", list(SALES_ORDER_FIELDS), SALES_ORDER_FIELDS, expanded)
        return JSONResponse(
            {"@odata.context": context + "/$entity", "@odata.etag": etag(order)}
            | order_row(order, None, expanded)
        )

    @router.get("/SalesOrder('{key}')/_Item")
    def list_items(
        key: str,
        request: Request,
        filter_text: str | None = Query(None, alias="$filter"),
        select: str | None = Query(None, alias="$select"),
        orderby: str | None = Query(None, alias="$orderby"),
        top: str | None = Query(None, alias="$top"),
        skip: str | None = Query(None, alias="$skip"),
        count: str | None = Query(None, alias="$count"),
    ):
        reject_unsupported(request, LIST_OPTIONS)
        query = ListQuery(filter_text, select, orderby, top, skip, count)
        result = ListSalesOrderItems(repo).execute(key, query)
        entity = f"SalesOrder('{key}')/_Item"
        body = {"@odata.context": context_for(entity, result.select, SALES_ORDER_ITEM_FIELDS, False)}
        if result.total is not None:
            body["@odata.count"] = result.total
        body["value"] = [item_to_json(item, result.select) for item in result.rows]
        return body

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

    @app.exception_handler(InvalidQuery)
    def invalid_query(request: Request, error: InvalidQuery):
        return JSONResponse(
            error_body("INVALID_QUERY", error.message, error.target), status_code=400
        )

    @app.exception_handler(UnsupportedQueryOption)
    def unsupported_query_option(request: Request, error: UnsupportedQueryOption):
        return JSONResponse(
            error_body("UNSUPPORTED_QUERY_OPTION", error.message, error.target),
            status_code=400,
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
