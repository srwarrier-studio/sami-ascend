from collections.abc import Callable
from datetime import date

from fastapi import APIRouter, Depends
from token_verification import Role
from token_verification.fastapi_deps import AuthDependencies

from synapse_api.application.read_records import ReadRecords
from synapse_api.application.sales_cache import SalesCache
from synapse_api.domain.entities.registry import Registry
from synapse_api.domain.gateways.record_source import RecordSource
from synapse_api.infrastructure.api.records.schemas import RecordsResponse, RecordTypesResponse


def create_records_router(
    source: RecordSource, registry: Registry, auth: AuthDependencies, today: Callable[[], date], cache: SalesCache
) -> APIRouter:
    router = APIRouter(dependencies=[Depends(auth.require_roles(Role.MANAGEMENT, Role.ADMIN))])

    @router.get("/records/types")
    def record_types() -> RecordTypesResponse:
        return RecordTypesResponse.from_domain(list(registry.records.values()))

    @router.get("/records")
    def records(
        type: str, key: str, key_field: str | None = None, start: date | None = None, end: date | None = None
    ) -> RecordsResponse:
        def load() -> RecordsResponse:
            field, rows = ReadRecords(source, registry).execute(type, key, key_field, start, end, today())
            return RecordsResponse(type=type, key_field=field, key=key, start=start, end=end, records=rows)

        return cache.get(("records", type, key, key_field, start, end, today()), load)

    return router
