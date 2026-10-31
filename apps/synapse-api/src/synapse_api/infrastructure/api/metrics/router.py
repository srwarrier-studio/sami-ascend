from collections.abc import Callable
from datetime import date

from fastapi import APIRouter, Depends
from token_verification import Role
from token_verification.fastapi_deps import AuthDependencies

from synapse_api.application.compare_metric import CompareMetric
from synapse_api.application.month_figure import GetMonthFigure
from synapse_api.application.sales_cache import SalesCache
from synapse_api.domain.entities.registry import Registry
from synapse_api.domain.gateways.metric_source import MetricSource
from synapse_api.infrastructure.api.metrics.schemas import CompareResponse, MetricsResponse, MonthResponse


def create_metrics_router(
    source: MetricSource, registry: Registry, auth: AuthDependencies, today: Callable[[], date], cache: SalesCache
) -> APIRouter:
    router = APIRouter(dependencies=[Depends(auth.require_roles(Role.MANAGEMENT, Role.ADMIN))])

    @router.get("/metrics")
    def list_metrics() -> MetricsResponse:
        return MetricsResponse.from_domain(list(registry.metrics.values()))

    @router.get("/metrics/{metric}/compare")
    def compare(
        metric: str, start: date, end: date, compare_start: date, compare_end: date, by: str | None = None, top: int = 10
    ) -> CompareResponse:
        return cache.get(
            ("compare", metric, start, end, compare_start, compare_end, by, top),
            lambda: CompareResponse.from_domain(
                CompareMetric(source, registry).execute(metric, start, end, compare_start, compare_end, by, top)
            ),
        )

    @router.get("/metrics/{metric}/month")
    def month(metric: str, month: str, trend: int = 6) -> MonthResponse:
        return cache.get(
            ("month", metric, today(), month, trend),
            lambda: MonthResponse.from_domain(GetMonthFigure(source, registry).execute(metric, today(), month, trend)),
        )

    return router
