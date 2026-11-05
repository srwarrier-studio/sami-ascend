from dataclasses import dataclass
from functools import wraps

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from butterfly.application.filter.fields import STANDARD_PLANT_FIELDS
from butterfly.application.filter.parser import parse_filter
from butterfly.domain.entities.master_data import PURCHASING_ORGANIZATIONS, SALES_ORGANIZATIONS
from butterfly.domain.errors import InvalidQuery
from butterfly.domain.repositories.master_data_repo import MasterDataRepo
from butterfly.infrastructure.api.standard import v4
from butterfly.infrastructure.api.standard.dialects import V4_MEDIA, Refusal
from butterfly.infrastructure.api.standard.edmx import PLANT_METADATA, load

ROOT = "/sap/opu/odata4/sap/api_plant_2/srvd_a2x/sap/plant/0001"
METADATA_ETAG = 'W/"20260727125802"'
ETAG = ""
LIST_OPTIONS = {"$filter", "$select", "$orderby", "$top", "$skip", "$count", "$expand", "$format"}
KEYS = ("Plant",)


@dataclass(frozen=True)
class PlantRow:
    plant: str
    name: str
    sales_organization: str
    purchasing_organization: str
    distribution_channel: str = "10"
    division: str = "00"
    language: str = "EN"


class Service:
    def __init__(self, master_data: MasterDataRepo):
        self.master_data = master_data
        self.metadata = load(PLANT_METADATA)
        self.type = self.metadata.types["PlantType"]

    def rows(self) -> list[PlantRow]:
        return [
            PlantRow(p.plant, p.name, SALES_ORGANIZATIONS[p.company_code], PURCHASING_ORGANIZATIONS[p.company_code])
            for p in self.master_data.list_plants()
        ]

    def row(self, source: PlantRow, select: list[str] | None) -> dict:
        values = {
            "Plant": source.plant,
            "PlantName": source.name,
            "ValuationArea": source.plant,
            "SalesOrganization": source.sales_organization,
            "DefaultPurchasingOrganization": source.purchasing_organization,
            "DistributionChannel": source.distribution_channel,
            "Division": source.division,
            "Language": source.language,
        }
        row = v4.row_of(self.type, values, ETAG, select, KEYS)
        del row["@odata.etag"]
        return row

    def no_expand(self, request: Request) -> None:
        text = request.query_params.get("$expand")
        if text is not None:
            raise Refusal("expand", text.strip().split("(")[0])

    def list_of(self, request: Request) -> dict:
        v4.check_options(request, LIST_OPTIONS)
        self.no_expand(request)
        select = v4.selection(request.query_params.get("$select"), self.type)
        result = v4.listing(request, self.rows(), STANDARD_PLANT_FIELDS)
        return v4.list_body(v4.context("Plant", select, None, "", KEYS), [self.row(r, select) for r in result.rows], result.total, METADATA_ETAG)

    def entity_of(self, request: Request, key: str) -> dict:
        v4.check_options(request, {"$select", "$expand", "$format"})
        self.no_expand(request)
        select = v4.selection(request.query_params.get("$select"), self.type)
        found = next((r for r in self.rows() if r.plant == key), None)
        if found is None:
            raise Refusal("missing")
        return v4.entity_body(v4.context("Plant", select, None, "", KEYS), self.row(found, select), METADATA_ETAG)

    def count(self, request: Request) -> Response:
        text = request.query_params.get("$filter")
        try:
            condition = None if text is None else parse_filter(text, STANDARD_PLANT_FIELDS)
        except InvalidQuery as error:
            raise Refusal("parse", text.split(" ")[0]) from error
        rows = [r for r in self.rows() if condition is None or condition.matches(r)]
        return Response(str(len(rows)), media_type="text/plain; charset=utf-8")


def build_plant_router(master_data: MasterDataRepo) -> APIRouter:
    service = Service(master_data)
    router = APIRouter(prefix=ROOT)

    def guarded(function):
        @wraps(function)
        def handler(*args, **kwargs):
            try:
                outcome = function(*args, **kwargs)
            except Refusal as error:
                status, body = v4.refusal_response(error, "LO-MD-PL", "API_PLANT_2")
                return JSONResponse(body, status_code=status, media_type=V4_MEDIA)
            return outcome if isinstance(outcome, Response) else JSONResponse(outcome, media_type=V4_MEDIA)

        return handler

    @router.get("/$metadata")
    def metadata():
        return Response(service.metadata.content(), media_type="application/xml")

    @router.get("/Plant/$count")
    @guarded
    def count(request: Request):
        return service.count(request)

    @router.get("/Plant")
    @guarded
    def listing(request: Request):
        return service.list_of(request)

    @router.get("/Plant('{key}')")
    @guarded
    def one(request: Request, key: str):
        return service.entity_of(request, key)

    return router
