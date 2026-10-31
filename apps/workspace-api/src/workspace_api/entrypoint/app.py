from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from structured_logging import RequestIdMiddleware
from structured_logging import get_request_id
from token_verification import Role, TokenVerifier
from token_verification.fastapi_deps import AuthDependencies
from token_verification.token_claims import TokenClaims

from workspace_api.application.usecase.create_sales_order import CreateSalesOrder, Submitter
from workspace_api.application.usecase.list_sales_orders import ListSalesOrders
from workspace_api.domain.entities.order_request import OrderRequest
from workspace_api.domain.errors import InvalidQuery, SalesOrderRejected, SapUnavailable, StoreUnavailable
from workspace_api.domain.gateways.sales_order_gateway import SalesOrderGateway
from workspace_api.domain.repositories.order_request_store import OrderRequestStore
from workspace_api.entrypoint.schemas import (
    NewSalesOrderBody,
    OrderRequestResponse,
    OrderRequestsResponse,
    SalesOrderPageResponse,
    SalesOrderResponse,
)
from workspace_api.infrastructure.settings import Settings


def create_app(gateway: SalesOrderGateway, settings: Settings, orders: OrderRequestStore | None = None) -> FastAPI:
    auth = AuthDependencies(TokenVerifier(settings.jwt_secret))
    sales_only = Depends(auth.require_roles(Role.SALES))
    router = APIRouter(dependencies=[sales_only])

    @router.post("/sales-orders", status_code=201, response_model=SalesOrderResponse)
    def create_sales_order(body: NewSalesOrderBody, claims: Annotated[TokenClaims, sales_only]):
        submitter = Submitter(claims.userid, claims.sap_username, get_request_id())
        result = CreateSalesOrder(gateway, orders).execute(body.to_domain(), submitter)
        if isinstance(result, OrderRequest):
            return JSONResponse(OrderRequestResponse.from_domain(result).model_dump(mode="json"), status_code=202)
        return SalesOrderResponse.from_domain(result)

    @router.get("/sales-orders")
    def list_sales_orders(top: int = 20, skip: int = 0) -> SalesOrderPageResponse:
        page = ListSalesOrders(gateway).execute(top, skip)
        return SalesOrderPageResponse.from_domain(page)

    if orders is not None:

        @router.get("/sales-order-requests/{request_id}")
        def order_request(request_id: str, claims: Annotated[TokenClaims, sales_only]) -> OrderRequestResponse:
            found = orders.get(request_id, claims.userid)
            if found is None:
                raise HTTPException(status_code=404, detail="No such order request")
            return OrderRequestResponse.from_domain(found)

        @router.get("/sales-order-requests")
        def open_order_requests(claims: Annotated[TokenClaims, sales_only], open: bool = True) -> OrderRequestsResponse:
            if not open:
                raise InvalidQuery("only open=true is supported")
            return OrderRequestsResponse(requests=[OrderRequestResponse.from_domain(r) for r in orders.list_open(claims.userid, 50)])

    app = FastAPI()

    @app.exception_handler(StoreUnavailable)
    def store_unavailable(request: Request, error: StoreUnavailable) -> JSONResponse:
        return JSONResponse({"code": "STORE_UNAVAILABLE"}, status_code=503)

    @app.exception_handler(SalesOrderRejected)
    def rejected(request: Request, error: SalesOrderRejected) -> JSONResponse:
        details = [{"code": d.code, "target": d.target, "message": d.message} for d in error.details]
        return JSONResponse({"code": "VALIDATION_FAILED", "details": details}, status_code=422)

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
    app.include_router(router, prefix="/v1/workspace", tags=["Sales orders"])
    return app
