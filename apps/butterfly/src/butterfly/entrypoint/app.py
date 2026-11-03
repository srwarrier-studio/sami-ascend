import json
import logging
import os
from pathlib import Path
from datetime import date, datetime
from typing import Callable

import uvicorn
from fastapi import APIRouter, FastAPI, Query, Request
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from structured_logging import RequestIdMiddleware, get_request_id, setup_logging

from butterfly.application.dto.list_query_dto import ListQuery
from butterfly.application.filter.fields import (
    CUSTOMER_INVOICE_FIELDS,
    PRODUCTION_ORDER_COMPONENT_FIELDS,
    PRODUCTION_ORDER_FIELDS,
    PURCHASE_DELIVERY_FIELDS,
    RECEIVABLES_AGEING_FIELDS,
    RECEIVABLES_BY_CUSTOMER_FIELDS,
    RECEIVABLES_SUMMARY_FIELDS,
    SALES_CONTRACT_FIELDS,
    SALES_ORDER_FIELDS,
    SALES_ORDER_ITEM_FIELDS,
    SALES_SUMMARY_BY_CUSTOMER_FIELDS,
    SALES_SUMMARY_BY_DAY_FIELDS,
    PURCHASE_SUMMARY_BY_DAY_FIELDS,
    PURCHASE_SUMMARY_BY_MATERIAL_FIELDS,
    PURCHASE_SUMMARY_BY_SUPPLIER_FIELDS,
    SALES_SUMMARY_BY_MATERIAL_FIELDS,
)
from butterfly.application.query_options import parse_expand
from butterfly.application.usecase.change_sales_order import ChangeSalesOrder
from butterfly.application.usecase.create_sales_order import CreateSalesOrder, utc_now
from butterfly.application.usecase.get_sales_order import GetSalesOrder
from butterfly.application.usecase.list_sales_order_items import ListSalesOrderItems
from butterfly.application.usecase.list_sales_orders import ListSalesOrders
from butterfly.application.usecase.list_sales_summary import ListSalesSummary
from butterfly.application.usecase.summarize_purchases_by_day import SummarizePurchasesByDay
from butterfly.application.usecase.summarize_purchases_by_material import SummarizePurchasesByMaterial
from butterfly.application.usecase.summarize_purchases_by_supplier import SummarizePurchasesBySupplier
from butterfly.application.usecase.summarize_receivables import SummarizeReceivables
from butterfly.application.usecase.summarize_receivables_ageing import SummarizeReceivablesAgeing
from butterfly.application.usecase.summarize_receivables_by_customer import SummarizeReceivablesByCustomer
from butterfly.application.usecase.summarize_by_customer import SummarizeByCustomer
from butterfly.application.usecase.summarize_by_day import SummarizeByDay
from butterfly.application.usecase.summarize_by_material import SummarizeByMaterial
from butterfly.domain.errors import (
    ETagMismatch,
    ETagRequired,
    InvalidQuery,
    SalesOrderNotFound,
    UnsupportedQueryOption,
    ValidationFailed,
)
from butterfly.domain.repositories.driver_repo import DriverRepo
from butterfly.domain.repositories.master_data_repo import MasterDataRepo
from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo
from butterfly.infrastructure.api.odata import (
    DRIVERS_ROOT,
    ROOT,
    error_body,
    item_to_json,
    order_to_json,
    summary_to_json,
)
from butterfly.infrastructure.memory.in_memory_driver_repo import InMemoryDriverRepo
from butterfly.infrastructure.memory.in_memory_master_data_repo import InMemoryMasterDataRepo
from butterfly.infrastructure.memory.scenarios import find_scenario
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.driver_repo import SqliteDriverRepo
from butterfly.infrastructure.sqlite.master_data_repo import SqliteMasterDataRepo
from butterfly.infrastructure.sqlite.sales_order_repo import SqliteSalesOrderRepo
from butterfly.infrastructure.sqlite.seeder import SEEDS, prepare

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


HTTP_ERRORS = {
    404: ("RESOURCE_NOT_FOUND", "The requested resource does not exist."),
    405: ("METHOD_NOT_ALLOWED", "This method is not supported for this resource."),
}


def create_app(
    repo: SalesOrderRepo,
    master_data: MasterDataRepo | None = None,
    drivers: DriverRepo | None = None,
    now: Callable[[], datetime] = utc_now,
) -> FastAPI:
    master_data = master_data or InMemoryMasterDataRepo()
    drivers = drivers or InMemoryDriverRepo()
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
            {"@odata.context": context + "/$entity", "@odata.etag": order.etag}
            | order_row(order, None, expanded)
        )

    @router.post("/SalesOrder")
    async def create_order(request: Request):
        try:
            payload = json.loads(await request.body())
        except ValueError:
            payload = None
        if not isinstance(payload, dict):
            return JSONResponse(
                error_body("INVALID_REQUEST_BODY", "The request body must be a JSON object.", "body"),
                status_code=400,
            )
        order = CreateSalesOrder(repo, master_data, now).execute(payload)
        location = f"{str(request.base_url).rstrip('/')}{ROOT}SalesOrder('{order.sales_order}')"
        context = context_for("SalesOrder", list(SALES_ORDER_FIELDS), SALES_ORDER_FIELDS, True)
        return JSONResponse(
            {"@odata.context": context + "/$entity", "@odata.etag": order.etag}
            | order_row(order, None, True),
            status_code=201,
            headers={"Location": location},
        )

    @router.patch("/SalesOrder('{key}')")
    async def change_order(key: str, request: Request):
        try:
            payload = json.loads(await request.body())
        except ValueError:
            payload = None
        if not isinstance(payload, dict):
            return JSONResponse(
                error_body("INVALID_REQUEST_BODY", "The request body must be a JSON object.", "body"),
                status_code=400,
            )
        order = ChangeSalesOrder(repo, now).execute(key, request.headers.get("if-match"), payload)
        return JSONResponse(
            {"@odata.context": "$metadata#SalesOrder/$entity", "@odata.etag": order.etag}
            | order_to_json(order)
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

    def add_list_route(target: APIRouter, entity: str, rows: Callable[[], list], fields: dict):
        @target.get("/" + entity)
        def list_rows(
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
            result = ListSalesSummary(rows, fields).execute(query)
            body = {"@odata.context": context_for(entity, result.select, fields, False)}
            if result.total is not None:
                body["@odata.count"] = result.total
            body["value"] = [summary_to_json(row, fields, result.select) for row in result.rows]
            return body

    def as_of_date(text: str | None) -> date:
        if text is None:
            return now().date()
        try:
            return date.fromisoformat(text)
        except ValueError:
            raise InvalidQuery("AsOfDate must be a date like 2026-10-31.", "AsOfDate")

    def add_receivables_route(target: APIRouter, entity: str, summarize, fields: dict):
        @target.get("/" + entity)
        def list_receivables(
            request: Request,
            as_of: str | None = Query(None, alias="AsOfDate"),
            filter_text: str | None = Query(None, alias="$filter"),
            select: str | None = Query(None, alias="$select"),
            orderby: str | None = Query(None, alias="$orderby"),
            top: str | None = Query(None, alias="$top"),
            skip: str | None = Query(None, alias="$skip"),
            count: str | None = Query(None, alias="$count"),
        ):
            reject_unsupported(request, LIST_OPTIONS)
            day = as_of_date(as_of)
            query = ListQuery(filter_text, select, orderby, top, skip, count)
            result = ListSalesSummary(lambda: drivers.summary_listing(entity, day) or summarize(drivers).execute(day), fields).execute(query)
            body = {"@odata.context": context_for(entity, result.select, fields, False)}
            if result.total is not None:
                body["@odata.count"] = result.total
            body["value"] = [summary_to_json(row, fields, result.select) for row in result.rows]
            return body

    def add_summary_route(entity: str, summarize, fields: dict):
        add_list_route(router, entity, lambda: repo.summary_listing(entity) or summarize(repo).execute(), fields)

    add_summary_route("SalesSummaryByDay", SummarizeByDay, SALES_SUMMARY_BY_DAY_FIELDS)
    add_summary_route("SalesSummaryByCustomer", SummarizeByCustomer, SALES_SUMMARY_BY_CUSTOMER_FIELDS)
    add_summary_route("SalesSummaryByMaterial", SummarizeByMaterial, SALES_SUMMARY_BY_MATERIAL_FIELDS)

    drivers_router = APIRouter(prefix=DRIVERS_ROOT.rstrip("/"))
    add_list_route(drivers_router, "SalesContract", lambda: drivers.listing("contracts"), SALES_CONTRACT_FIELDS)
    add_list_route(drivers_router, "PurchaseDelivery", lambda: drivers.listing("deliveries"), PURCHASE_DELIVERY_FIELDS)
    add_list_route(drivers_router, "CustomerInvoice", lambda: drivers.listing("invoices"), CUSTOMER_INVOICE_FIELDS)
    add_receivables_route(drivers_router, "ReceivablesSummary", SummarizeReceivables, RECEIVABLES_SUMMARY_FIELDS)
    add_receivables_route(drivers_router, "ReceivablesByCustomer", SummarizeReceivablesByCustomer, RECEIVABLES_BY_CUSTOMER_FIELDS)
    add_receivables_route(drivers_router, "ReceivablesAgeing", SummarizeReceivablesAgeing, RECEIVABLES_AGEING_FIELDS)
    add_list_route(drivers_router, "ProductionOrder", lambda: drivers.listing("production_orders"), PRODUCTION_ORDER_FIELDS)
    add_list_route(drivers_router, "ProductionOrderComponent", lambda: drivers.listing("components"), PRODUCTION_ORDER_COMPONENT_FIELDS)
    add_list_route(drivers_router, "PurchaseSummaryByDay", lambda: drivers.summary_listing("PurchaseSummaryByDay") or SummarizePurchasesByDay(drivers).execute(), PURCHASE_SUMMARY_BY_DAY_FIELDS)
    add_list_route(drivers_router, "PurchaseSummaryBySupplier", lambda: drivers.summary_listing("PurchaseSummaryBySupplier") or SummarizePurchasesBySupplier(drivers).execute(), PURCHASE_SUMMARY_BY_SUPPLIER_FIELDS)
    add_list_route(drivers_router, "PurchaseSummaryByMaterial", lambda: drivers.summary_listing("PurchaseSummaryByMaterial") or SummarizePurchasesByMaterial(drivers).execute(), PURCHASE_SUMMARY_BY_MATERIAL_FIELDS)

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

    @app.exception_handler(ValidationFailed)
    def validation_failed(request: Request, error: ValidationFailed):
        details = [
            {"code": d.code, "message": d.message, "target": d.target} for d in error.details
        ]
        return JSONResponse(
            error_body("VALIDATION_FAILED", "The sales order has errors.", details=details),
            status_code=400,
        )

    @app.exception_handler(ETagRequired)
    def etag_required(request: Request, error: ETagRequired):
        return JSONResponse(
            error_body(
                "ETAG_REQUIRED",
                "An If-Match header with the etag from the last read is required.",
                "SalesOrder",
            ),
            status_code=428,
        )

    @app.exception_handler(ETagMismatch)
    def etag_mismatch(request: Request, error: ETagMismatch):
        return JSONResponse(
            error_body(
                "ETAG_MISMATCH",
                "The sales order was changed by someone else. Reload and try again.",
                "SalesOrder",
            ),
            status_code=412,
        )

    @app.exception_handler(StarletteHTTPException)
    def http_error(request: Request, error: StarletteHTTPException):
        code, message = HTTP_ERRORS.get(error.status_code, ("HTTP_ERROR", str(error.detail)))
        return JSONResponse(
            error_body(code, message),
            status_code=error.status_code,
            headers=getattr(error, "headers", None),
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
    app.include_router(drivers_router)
    return app


DEFAULT_DB = Path(__file__).resolve().parents[3] / "butterfly.db"


def build_default_app(today: date, seed_name: str | None = None, scenario_name: str | None = None, db_path: str | None = None) -> FastAPI:
    name = seed_name if seed_name is not None else os.environ.get("BUTTERFLY_SEED", "story")
    scenario = scenario_name if scenario_name is not None else os.environ.get("BUTTERFLY_SCENARIO", "august-contract")
    if name not in SEEDS:
        raise SystemExit(f"BUTTERFLY_SEED must be 'story' or 'small', not '{name}'")
    if name == "story":
        find_scenario(scenario)
    db = Database(db_path if db_path is not None else os.environ.get("BUTTERFLY_DB", str(DEFAULT_DB)))
    prepare(db, name, scenario, today)
    return create_app(SqliteSalesOrderRepo(db), master_data=SqliteMasterDataRepo(db), drivers=SqliteDriverRepo(db))


setup_logging("butterfly")
app = build_default_app(date.today())


def main():
    uvicorn.run(app, host="0.0.0.0", port=8003, log_config=None)


if __name__ == "__main__":
    main()
