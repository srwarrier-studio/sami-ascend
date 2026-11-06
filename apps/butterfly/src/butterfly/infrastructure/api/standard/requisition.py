import inspect
import json
import re
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from functools import wraps

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from butterfly.application.alpha import external
from butterfly.application.filter.fields import STANDARD_REQUISITION_FIELDS, STANDARD_REQUISITION_ITEM_FIELDS
from butterfly.application.filter.parser import parse_filter
from butterfly.domain.entities.master_data import ISO_UNITS
from butterfly.domain.entities.purchase_requisition import PurchaseRequisition, PurchaseRequisitionItem
from butterfly.application.usecase.change_purchase_requisition_item import (
    ChangePurchaseRequisitionItem,
    DeletePurchaseRequisitionItem,
    RequisitionNotFound,
)
from butterfly.application.usecase.create_purchase_requisition import CreatePurchaseRequisition
from butterfly.application.usecase.create_sales_order import utc_now
from butterfly.domain.entities.release_rule import RELEASE_RULES, ReleaseRule
from butterfly.domain.errors import ETagMismatch, ETagRequired, InvalidQuery, ValidationDetail, ValidationFailed
from butterfly.domain.repositories.master_data_repo import MasterDataRepo
from butterfly.domain.repositories.purchase_requisition_repo import PurchaseRequisitionRepo
from butterfly.infrastructure.api.standard.dialects import V4_MEDIA, Refusal
from butterfly.infrastructure.api.standard import v4
from butterfly.infrastructure.api.standard.edmx import REQUISITION_METADATA, EntityType, load

ROOT = "/sap/opu/odata4/sap/api_purchaserequisition_2/srvd_a2x/sap/purchaserequisition/0001"
METADATA_ETAG = 'W/"20260727114643"'
HEADERS, ITEMS = "PurchaseReqn", "PurchaseReqnItem"
ITEMS_OF_HEADER, HEADER_OF_ITEM = "_PurchaseRequisitionItem", "_PurReqn"
HEADER_KEYS = ("PurchaseRequisition",)
ITEM_KEYS = ("PurchaseRequisition", "PurchaseRequisitionItem")
LIST_OPTIONS = {"$filter", "$select", "$orderby", "$top", "$skip", "$count", "$expand", "$format"}
EXPAND = re.compile(r"(_\w+)(?:\(\$select=([^)]*)\))?")
NUMBER_STRINGS = {"PurchasingDocumentItem", "PurchaseContractItem", "Reservation"}


@dataclass(frozen=True)
class ItemRow(PurchaseRequisitionItem):
    created_by_user: str = ""
    creation_date: date | None = None
    etag: str = ""


def item_rows(requisition: PurchaseRequisition) -> list[ItemRow]:
    created = requisition.creation_date_time.astimezone(timezone.utc).date()
    return [ItemRow(**vars(item), created_by_user=requisition.created_by_user, creation_date=created, etag=requisition.etag) for item in requisition.items]


def row_of(entity_type: EntityType, values: dict, etag: str, select: list[str] | None, keys: tuple[str, ...]) -> dict:
    return v4.row_of(entity_type, values, etag, select, keys, frozenset(NUMBER_STRINGS))


class Service:
    def __init__(self, repo: PurchaseRequisitionRepo):
        self.repo = repo
        self.metadata = load(REQUISITION_METADATA)
        self.header_type = self.metadata.types["PurchaseReqnType"]
        self.item_type = self.metadata.types["PurchaseReqnItemType"]

    def header_values(self, requisition: PurchaseRequisition) -> dict:
        return {
            "PurchaseRequisition": requisition.purchase_requisition,
            "PurchaseRequisitionType": requisition.requisition_type,
            "PurReqnDescription": requisition.description,
        }

    def item_values(self, item: ItemRow) -> dict:
        return {
            "PurchaseRequisition": item.purchase_requisition,
            "PurchaseRequisitionItem": item.purchase_requisition_item,
            "PurchasingDocument": item.purchasing_document,
            "PurchasingDocumentItem": item.purchasing_document_item or "0",
            "PurReqnReleaseStatus": item.release_status,
            "PurchaseRequisitionItemText": item.item_text,
            "Material": item.material,
            "MaterialGroup": item.material_group,
            "RequestedQuantity": float(item.requested_quantity),
            "BaseUnit": item.base_unit,
            "BaseUnitISOCode": ISO_UNITS.get(item.base_unit, item.base_unit),
            "PurchaseRequisitionPrice": float(item.price),
            "PurReqnPriceQuantity": 1,
            "PurchasingOrganization": item.purchasing_organization,
            "PurchasingGroup": item.purchasing_group,
            "Plant": item.plant,
            "CompanyCode": item.company_code,
            "OrderedQuantity": float(item.ordered_quantity),
            "DeliveryDate": item.delivery_date.isoformat(),
            "ProcessingStatus": item.processing_status,
            "Supplier": external(item.supplier),
            "IsDeleted": item.is_deleted,
            "CreatedByUser": item.created_by_user,
            "PurReqCreationDate": item.creation_date.isoformat() if item.creation_date else None,
            "PurReqnItemCurrency": item.currency,
            "ItemNetAmount": float(item.net_amount),
            "ReleaseIsNotCompleted": item.release_is_not_completed,
            "GoodsReceiptIsExpected": True,
            "InvoiceIsExpected": True,
        }

    def item_row(self, item: ItemRow, select: list[str] | None, header: PurchaseRequisition | None = None) -> dict:
        row = row_of(self.item_type, self.item_values(item), item.etag, select, ("PurchaseRequisition", "PurchaseRequisitionItem"))
        if header is not None:
            row[HEADER_OF_ITEM] = self.header_row(header, None, None)
        return row

    def header_row(self, requisition: PurchaseRequisition, select: list[str] | None, expand: list[str] | None) -> dict:
        row = row_of(self.header_type, self.header_values(requisition), requisition.etag, select, ("PurchaseRequisition",))
        if expand is not None:
            row[ITEMS_OF_HEADER] = [self.item_row(item, expand or None) for item in item_rows(requisition)]
        return row

    def selection(self, text: str | None, entity_type: EntityType) -> list[str] | None:
        return v4.selection(text, entity_type)

    def expansion(self, text: str | None, expected: str) -> list[str] | None:
        if text is None:
            return None
        found = EXPAND.fullmatch(text.strip())
        if found is None or found.group(1) != expected:
            raise Refusal("expand", found.group(1) if found else text.strip())
        return found.group(2).split(",") if found.group(2) else []

    def check_options(self, request: Request, allowed: set[str]) -> None:
        v4.check_options(request, allowed)

    def listing(self, request: Request, rows: list, fields: dict):
        return v4.listing(request, rows, fields)

    def context(self, entity: str, select: list[str] | None, expand: list[str] | None, nav: str) -> str:
        keys = HEADER_KEYS if entity == HEADERS else ITEM_KEYS
        return v4.context(entity, select, expand, nav if expand is not None else "", keys, ITEM_KEYS if entity == HEADERS else HEADER_KEYS)

    def list_body(self, context: str, rows: list, total: int | None) -> dict:
        return v4.list_body(context, rows, total, METADATA_ETAG)

    def entity_body(self, context: str, row: dict) -> dict:
        return v4.entity_body(context, row, METADATA_ETAG)

    def find(self, key: str) -> PurchaseRequisition:
        requisition = self.repo.get(key)
        if requisition is None:
            raise Refusal("missing")
        return requisition

    def all_items(self) -> list[ItemRow]:
        return [item for requisition in self.repo.list_all() for item in item_rows(requisition)]

    def header_list(self, request: Request) -> dict:
        self.check_options(request, LIST_OPTIONS)
        select = self.selection(request.query_params.get("$select"), self.header_type)
        expand = self.expansion(request.query_params.get("$expand"), ITEMS_OF_HEADER)
        result = self.listing(request, self.repo.list_all(), STANDARD_REQUISITION_FIELDS)
        rows = [self.header_row(requisition, select, expand) for requisition in result.rows]
        return self.list_body(self.context(HEADERS, select, expand, ITEMS_OF_HEADER), rows, result.total)

    def header_entity(self, request: Request, key: str) -> dict:
        self.check_options(request, {"$select", "$expand", "$format"})
        select = self.selection(request.query_params.get("$select"), self.header_type)
        expand = self.expansion(request.query_params.get("$expand"), ITEMS_OF_HEADER)
        row = self.header_row(self.find(key), select, expand)
        return self.entity_body(self.context(HEADERS, select, expand, ITEMS_OF_HEADER), row)

    def items_of_header(self, request: Request, key: str) -> dict:
        self.check_options(request, LIST_OPTIONS)
        select = self.selection(request.query_params.get("$select"), self.item_type)
        result = self.listing(request, item_rows(self.find(key)), STANDARD_REQUISITION_ITEM_FIELDS)
        return self.list_body(f"$metadata#{ITEMS}", [self.item_row(item, select) for item in result.rows], result.total)

    def item_list(self, request: Request) -> dict:
        self.check_options(request, LIST_OPTIONS)
        select = self.selection(request.query_params.get("$select"), self.item_type)
        expand = self.expansion(request.query_params.get("$expand"), HEADER_OF_ITEM)
        result = self.listing(request, self.all_items(), STANDARD_REQUISITION_ITEM_FIELDS)
        headers = {r.purchase_requisition: r for r in self.repo.list_all()} if expand is not None else {}
        rows = [self.item_row(item, select, headers.get(item.purchase_requisition)) for item in result.rows]
        return self.list_body(self.context(ITEMS, select, expand, HEADER_OF_ITEM), rows, result.total)

    def item_entity(self, request: Request, key: str, item_key: str) -> dict:
        self.check_options(request, {"$select", "$format"})
        select = self.selection(request.query_params.get("$select"), self.item_type)
        for item in item_rows(self.find(key)):
            if item.purchase_requisition_item == item_key:
                return self.entity_body(self.context(ITEMS, select, None, ""), self.item_row(item, select))
        raise Refusal("missing")

    def count(self, request: Request, items: bool) -> Response:
        text = request.query_params.get("$filter")
        fields = STANDARD_REQUISITION_ITEM_FIELDS if items else STANDARD_REQUISITION_FIELDS
        try:
            condition = None if text is None else parse_filter(text, fields)
        except InvalidQuery as error:
            raise Refusal("parse", text.split(" ")[0]) from error
        rows = self.all_items() if items else self.repo.list_all()
        return Response(str(len([row for row in rows if condition is None or condition.matches(row)])), media_type="text/plain; charset=utf-8")

    def refusal(self, error: Refusal) -> tuple[int, dict]:
        return v4.refusal_response(error, "MM-PUR-REQ", "API_PURCHASEREQUISITION_2")


def failure(status: int, code: str, message: str, target: str | None = None, details: list[dict] | None = None) -> tuple[int, dict]:
    error = {"code": code, "message": message, "@SAP__common.ExceptionCategory": "Client_Error"}
    if target is not None:
        error["target"] = target
    if details is not None:
        error["details"] = details
    return status, {"error": error}


def domain_failure(error: Exception) -> tuple[int, dict] | None:
    if isinstance(error, ValidationFailed):
        details = [{"code": d.code, "message": d.message, "target": d.target} for d in error.details]
        return failure(400, "VALIDATION_FAILED", "The purchase requisition has errors.", details=details)
    if isinstance(error, ETagRequired):
        return failure(428, "ETAG_REQUIRED", "An If-Match header with the etag from the last read is required.")
    if isinstance(error, ETagMismatch):
        return failure(412, "ETAG_MISMATCH", "The purchase requisition was changed by someone else. Reload and try again.")
    if isinstance(error, RequisitionNotFound):
        return failure(404, "/IWBEP/CM_V4S_RUN/000", "Unspecified provider error occurred. See Error Context and Call Stack.")
    return None


def build_requisition_router(repo: PurchaseRequisitionRepo, master_data: MasterDataRepo, now: Callable[[], datetime] = utc_now, rules: tuple[ReleaseRule, ...] = RELEASE_RULES) -> APIRouter:
    service = Service(repo)
    router = APIRouter(prefix=ROOT)

    def answer(outcome):
        return outcome if isinstance(outcome, Response) else JSONResponse(outcome, media_type=V4_MEDIA)

    def refused(error: Exception):
        status, body = service.refusal(error) if isinstance(error, Refusal) else domain_failure(error)
        return JSONResponse(body, status_code=status, media_type=V4_MEDIA)

    caught = (Refusal, ValidationFailed, ETagRequired, ETagMismatch, RequisitionNotFound)

    def guarded(function):
        if inspect.iscoroutinefunction(function):

            @wraps(function)
            async def async_handler(*args, **kwargs):
                try:
                    return answer(await function(*args, **kwargs))
                except caught as error:
                    return refused(error)

            return async_handler

        @wraps(function)
        def handler(*args, **kwargs):
            try:
                return answer(function(*args, **kwargs))
            except caught as error:
                return refused(error)

        return handler

    @router.get("/$metadata")
    def metadata():
        return Response(service.metadata.content(), media_type="application/xml")

    @router.get(f"/{HEADERS}/$count")
    @guarded
    def header_count(request: Request):
        return service.count(request, items=False)

    @router.get(f"/{ITEMS}/$count")
    @guarded
    def item_count(request: Request):
        return service.count(request, items=True)

    @router.get(f"/{HEADERS}")
    @guarded
    def headers(request: Request):
        return service.header_list(request)

    @router.get(f"/{HEADERS}(" + "'{key}')")
    @guarded
    def header(request: Request, key: str):
        return service.header_entity(request, key)

    @router.get(f"/{HEADERS}(" + "'{key}')/" + ITEMS_OF_HEADER)
    @guarded
    def header_items(request: Request, key: str):
        return service.items_of_header(request, key)

    @router.get(f"/{ITEMS}")
    @guarded
    def items(request: Request):
        return service.item_list(request)

    @router.get(f"/{ITEMS}(PurchaseRequisition='" + "{key}',PurchaseRequisitionItem='{item_key}')")
    @guarded
    def item(request: Request, key: str, item_key: str):
        return service.item_entity(request, key, item_key)

    async def json_body(request: Request) -> dict:
        try:
            payload = json.loads(await request.body())
        except ValueError:
            payload = None
        if not isinstance(payload, dict):
            raise ValidationFailed([ValidationDetail("INVALID_REQUEST_BODY", "The request body must be a JSON object.", "body")])
        return payload

    @router.post(f"/{HEADERS}")
    @guarded
    async def create(request: Request):
        requisition = CreatePurchaseRequisition(repo, master_data, now, rules).execute(await json_body(request))
        row = service.header_row(requisition, None, [])
        location = f"{str(request.base_url).rstrip('/')}{ROOT}/{HEADERS}('{requisition.purchase_requisition}')"
        body = service.entity_body(service.context(HEADERS, None, [], ITEMS_OF_HEADER), row)
        return JSONResponse(body, status_code=201, headers={"Location": location}, media_type=V4_MEDIA)

    @router.patch(f"/{ITEMS}(PurchaseRequisition='" + "{key}',PurchaseRequisitionItem='{item_key}')")
    @guarded
    async def change(request: Request, key: str, item_key: str):
        use_case = ChangePurchaseRequisitionItem(repo, now, rules)
        requisition = use_case.execute(key, item_key, request.headers.get("if-match"), await json_body(request))
        return service.item_entity(request, requisition.purchase_requisition, item_key)

    @router.delete(f"/{ITEMS}(PurchaseRequisition='" + "{key}',PurchaseRequisitionItem='{item_key}')")
    @guarded
    def delete(request: Request, key: str, item_key: str):
        DeletePurchaseRequisitionItem(repo, now).execute(key, item_key, request.headers.get("if-match"))
        return Response(status_code=204)

    def add_empty(name: str):
        @router.get(f"/{name}")
        @guarded
        def empty(request: Request):
            return service.list_body(f"$metadata#{name}", [], None)

    for name in service.metadata.sets:
        if name not in (HEADERS, ITEMS):
            add_empty(name)

    return router
