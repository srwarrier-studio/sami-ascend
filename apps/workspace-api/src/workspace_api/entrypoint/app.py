from typing import Annotated

from fastapi import APIRouter, Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware
from structured_logging import RequestIdMiddleware
from token_verification import Role, TokenVerifier
from token_verification.fastapi_deps import AuthDependencies

from workspace_api.application.usecase.create_sales_order import CreateSalesOrder
from workspace_api.domain.gateways.sales_order_gateway import SalesOrderGateway
from workspace_api.entrypoint.schemas import NewSalesOrderBody, SalesOrderResponse
from workspace_api.infrastructure.settings import Settings


def create_app(gateway: SalesOrderGateway, settings: Settings) -> FastAPI:
    auth = AuthDependencies(TokenVerifier(settings.jwt_secret))
    sales_only = Depends(auth.require_roles(Role.SALES))
    router = APIRouter(dependencies=[sales_only])

    @router.post("/sales-orders", status_code=201)
    def create_sales_order(body: NewSalesOrderBody) -> SalesOrderResponse:
        order = CreateSalesOrder(gateway).execute(body.to_domain())
        return SalesOrderResponse.from_domain(order)

    app = FastAPI()
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
