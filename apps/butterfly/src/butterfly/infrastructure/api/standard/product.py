import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from butterfly.application.filter.fields import (
    STANDARD_PRODUCT_DESCRIPTION_FIELDS,
    STANDARD_PRODUCT_FIELDS,
    STANDARD_PRODUCT_PLANT_FIELDS,
    STANDARD_PRODUCT_UNIT_FIELDS,
)
from butterfly.application.filter.parser import parse_filter
from butterfly.domain.entities.master_data import PLANT_COMPANIES
from butterfly.domain.errors import InvalidQuery
from butterfly.domain.repositories.master_data_repo import MasterDataRepo
from butterfly.infrastructure.api.standard import v4
from butterfly.infrastructure.api.standard.dialects import V4_MEDIA, Refusal
from butterfly.infrastructure.api.standard.edmx import PRODUCT_METADATA, load

ROOT = "/sap/opu/odata4/sap/api_product/srvd_a2x/sap/product/0001"
METADATA_ETAG = 'W/"20261018074514"'
ETAG = 'W/"SADL-20260101000000"'
LANGUAGE = "EN"
LIST_OPTIONS = {"$filter", "$select", "$orderby", "$top", "$skip", "$count", "$expand", "$format"}
EXPAND = re.compile(r"(_\w+)(?:\(\$select=([^)]*)\))?")
LAMBDA = "_ProductDescription/any("
ZERO_STRINGS = frozenset({"CrossPlantStatus"})


@dataclass(frozen=True)
class ProductRow:
    product: str
    product_type: str
    product_group: str
    base_unit: str
    base_iso_unit: str
    division: str
    description: str


@dataclass(frozen=True)
class DescriptionRow:
    product: str
    language: str
    product_description: str


@dataclass(frozen=True)
class PlantRow:
    product: str
    plant: str
    base_unit: str
    base_iso_unit: str


@dataclass(frozen=True)
class UnitRow:
    product: str
    alternative_unit: str
    base_unit: str
    base_iso_unit: str


@dataclass(frozen=True)
class EntitySet:
    name: str
    type_name: str
    keys: tuple[str, ...]
    fields: dict
    rows: Callable[[], list]
    values: Callable[[object], dict]
    children: dict[str, str]


def rewrite_lambdas(text: str | None) -> str | None:
    while text is not None and LAMBDA in text:
        start = text.index(LAMBDA)
        found = re.match(r"(\w+):", text[start + len(LAMBDA) :])
        if found is None:
            raise Refusal("parse", text[start : start + 4])
        depth, end = 1, start + len(LAMBDA)
        while end < len(text) and depth:
            depth += {"(": 1, ")": -1}.get(text[end], 0)
            end += 1
        if depth:
            raise Refusal("parse", text[start : start + 4])
        inner = text[start + len(LAMBDA) + found.end() : end - 1].replace(f"{found.group(1)}/ProductDescription", "__description")
        text = text[:start] + f"({inner})" + text[end:]
    return text


class Service:
    def __init__(self, master_data: MasterDataRepo):
        self.master_data = master_data
        self.metadata = load(PRODUCT_METADATA)
        self.sets = {
            "Product": EntitySet(
                "Product", "Product_Type", ("Product",), STANDARD_PRODUCT_FIELDS, self.products, self.product_values,
                {"_ProductDescription": "ProductDescription", "_ProductPlant": "ProductPlant", "_ProductUnitOfMeasure": "ProductUnitOfMeasure"},
            ),
            "ProductDescription": EntitySet(
                "ProductDescription", "ProductDescription_Type", ("Product", "Language"), STANDARD_PRODUCT_DESCRIPTION_FIELDS, self.descriptions,
                lambda r: {"Product": r.product, "Language": r.language, "ProductDescription": r.product_description}, {},
            ),
            "ProductPlant": EntitySet(
                "ProductPlant", "ProductPlant_Type", ("Product", "Plant"), STANDARD_PRODUCT_PLANT_FIELDS, self.plants,
                lambda r: {"Product": r.product, "Plant": r.plant, "PeriodType": "M", "BaseUnit": r.base_unit, "BaseISOUnit": r.base_iso_unit}, {},
            ),
            "ProductUnitOfMeasure": EntitySet(
                "ProductUnitOfMeasure", "ProductUnitOfMeasure_Type", ("Product", "AlternativeUnit"), STANDARD_PRODUCT_UNIT_FIELDS, self.units,
                lambda r: {
                    "Product": r.product, "AlternativeUnit": r.alternative_unit, "QuantityNumerator": 1, "QuantityDenominator": 1,
                    "BaseUnit": r.base_unit, "BaseISOUnit": r.base_iso_unit,
                },
                {},
            ),
        }

    def products(self) -> list[ProductRow]:
        return [
            ProductRow(p.material_id, p.material_type, p.material_group, p.unit, p.iso_unit, "00", p.description)
            for p in self.master_data.list_products()
        ]

    def descriptions(self) -> list[DescriptionRow]:
        return [DescriptionRow(p.material_id, LANGUAGE, p.description) for p in self.master_data.list_products()]

    def plants(self) -> list[PlantRow]:
        return [
            PlantRow(p.material_id, plant, p.unit, p.iso_unit)
            for p in self.master_data.list_products()
            for plant, company in PLANT_COMPANIES.items()
            if company == p.company_code
        ]

    def units(self) -> list[UnitRow]:
        return [UnitRow(p.material_id, p.unit, p.unit, p.iso_unit) for p in self.master_data.list_products()]

    def product_values(self, row: ProductRow) -> dict:
        return {
            "Product": row.product,
            "ProductType": row.product_type,
            "ProductGroup": row.product_group,
            "BaseUnit": row.base_unit,
            "BaseISOUnit": row.base_iso_unit,
            "Division": row.division,
            "IsMarkedForDeletion": False,
            "CrossPlantStatus": "",
        }

    def row(self, entity: EntitySet, source, select: list[str] | None, expand: tuple[str, list[str]] | None = None) -> dict:
        row = v4.row_of(self.metadata.types[entity.type_name], entity.values(source), ETAG, select, entity.keys, ZERO_STRINGS)
        if expand is not None:
            child = self.sets[entity.children[expand[0]]]
            related = [r for r in child.rows() if r.product == source.product]
            row[expand[0]] = [self.row(child, r, expand[1] or None) for r in related]
        return row

    def expansion(self, text: str | None, entity: EntitySet) -> tuple[str, list[str]] | None:
        if text is None:
            return None
        found = EXPAND.fullmatch(text.strip())
        if found is None or found.group(1) not in entity.children:
            raise Refusal("expand", found.group(1) if found else text.strip())
        return found.group(1), found.group(2).split(",") if found.group(2) else []

    def condition(self, request: Request, fields: dict):
        text = rewrite_lambdas(request.query_params.get("$filter"))
        try:
            return text, None if text is None else parse_filter(text, fields)
        except InvalidQuery as error:
            raise Refusal("parse", (text or "").split(" ")[0]) from error

    def list_of(self, request: Request, entity: EntitySet, rows: list | None = None) -> dict:
        v4.check_options(request, LIST_OPTIONS)
        select = v4.selection(request.query_params.get("$select"), self.metadata.types[entity.type_name])
        expand = self.expansion(request.query_params.get("$expand"), entity)
        text = rewrite_lambdas(request.query_params.get("$filter"))
        result = v4.listing(request, entity.rows() if rows is None else rows, entity.fields, text)
        shown = [self.row(entity, r, select, expand) for r in result.rows]
        context = self.context(entity, select, expand)
        return v4.list_body(context, shown, result.total, METADATA_ETAG)

    def context(self, entity: EntitySet, select: list[str] | None, expand: tuple[str, list[str]] | None) -> str:
        child_keys = self.sets[entity.children[expand[0]]].keys if expand else ()
        return v4.context(entity.name, select, expand[1] if expand else None, expand[0] if expand else "", entity.keys, child_keys)

    def entity_of(self, request: Request, entity: EntitySet, keys: list[str]) -> dict:
        v4.check_options(request, {"$select", "$expand", "$format"})
        select = v4.selection(request.query_params.get("$select"), self.metadata.types[entity.type_name])
        expand = self.expansion(request.query_params.get("$expand"), entity)
        wanted = tuple(keys)
        found = next((r for r in entity.rows() if tuple(getattr(r, entity.fields[k][0]) for k in entity.keys) == wanted), None)
        if found is None:
            raise Refusal("missing")
        context = self.context(entity, select, expand)
        return v4.entity_body(context, self.row(entity, found, select, expand), METADATA_ETAG)

    def children_of(self, request: Request, entity: EntitySet, key: str, child_name: str) -> dict:
        found = next((r for r in entity.rows() if r.product == key), None)
        if found is None:
            raise Refusal("missing")
        child = self.sets[child_name]
        return self.list_of(request, child, [r for r in child.rows() if r.product == key])

    def count(self, request: Request, entity: EntitySet) -> Response:
        _, condition = self.condition(request, entity.fields)
        rows = [r for r in entity.rows() if condition is None or condition.matches(r)]
        return Response(str(len(rows)), media_type="text/plain; charset=utf-8")


def build_product_router(master_data: MasterDataRepo) -> APIRouter:
    service = Service(master_data)
    router = APIRouter(prefix=ROOT)

    def guarded(function):
        @wraps(function)
        def handler(*args, **kwargs):
            try:
                outcome = function(*args, **kwargs)
            except Refusal as error:
                status, body = v4.refusal_response(error, "LO-MD-MM", "API_PRODUCT")
                return JSONResponse(body, status_code=status, media_type=V4_MEDIA)
            return outcome if isinstance(outcome, Response) else JSONResponse(outcome, media_type=V4_MEDIA)

        return handler

    @router.get("/$metadata")
    def metadata():
        return Response(service.metadata.content(), media_type="application/xml")

    def add_routes(entity: EntitySet):
        @router.get(f"/{entity.name}/$count")
        @guarded
        def count(request: Request):
            return service.count(request, entity)

        @router.get(f"/{entity.name}")
        @guarded
        def listing(request: Request):
            return service.list_of(request, entity)

        if len(entity.keys) == 1:

            @router.get(f"/{entity.name}('{{k0}}')")
            @guarded
            def one(request: Request, k0: str):
                return service.entity_of(request, entity, [k0])

        else:
            first, second = entity.keys

            @router.get(f"/{entity.name}({first}='{{k0}}',{second}='{{k1}}')")
            @guarded
            def of_two(request: Request, k0: str, k1: str):
                return service.entity_of(request, entity, [k0, k1])

        for nav, child_name in entity.children.items():

            @router.get(f"/{entity.name}('{{k0}}')/{nav}")
            @guarded
            def children(request: Request, k0: str, child_name=child_name):
                return service.children_of(request, entity, k0, child_name)

    for entity in service.sets.values():
        add_routes(entity)

    def add_empty(name: str):
        @router.get(f"/{name}")
        @guarded
        def empty(request: Request):
            return v4.list_body(f"$metadata#{name}", [], None, METADATA_ETAG)

    for name in service.metadata.sets:
        if name not in service.sets:
            add_empty(name)

    return router
