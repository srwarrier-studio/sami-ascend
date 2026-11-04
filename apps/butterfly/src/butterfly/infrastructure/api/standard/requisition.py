import inspect
import json
import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from functools import wraps

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from butterfly.application.dto.list_query_dto import ListQuery
from butterfly.application.filter.fields import STANDARD_REQUISITION_FIELDS, STANDARD_REQUISITION_ITEM_FIELDS
from butterfly.application.filter.parser import parse_filter
from butterfly.application.list_query import apply_list_query
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
from butterfly.infrastructure.api.standard.dialects import V4_MEDIA, Refusal, short, stamp
from butterfly.infrastructure.api.standard.edmx import REQUISITION_METADATA, EntityType, load

ROOT = "/sap/opu/odata4/sap/api_purchaserequisition_2/srvd_a2x/sap/purchaserequisition/0001"
METADATA_ETAG = 'W/"20260727114643"'
HEADERS, ITEMS = "PurchaseReqn", "PurchaseReqnItem"
ITEMS_OF_HEADER, HEADER_OF_ITEM = "_PurchaseRequisitionItem", "_PurReqn"
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


def blank(edm: str):
    if edm == "Edm.String":
        return ""
    if edm == "Edm.Boolean":
        return False
    if edm == "Edm.Decimal":
        return 0
    if edm.startswith("Collection("):
        return []
    return None


def row_of(entity_type: EntityType, values: dict, etag: str, select: list[str] | None, keys: tuple[str, ...]) -> dict:
    row = {name: blank(edm) for name, edm in entity_type.properties}
    row |= {name: "0" for name in NUMBER_STRINGS & row.keys()}
    row |= {name: value for name, value in values.items() if name in row}
    names = None if select is None else [name for name, _ in entity_type.properties if name in select or name in keys]
    return {"@odata.etag": etag} | (row if names is None else {name: row[name] for name in names})


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
            "Supplier": item.supplier,
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
        if text is None:
            return None
        names = [name.strip() for name in text.split(",")]
        for name in names:
            if name not in entity_type.names():
                raise Refusal("property", name)
        return names

    def expansion(self, text: str | None, expected: str) -> list[str] | None:
        if text is None:
            return None
        found = EXPAND.fullmatch(text.strip())
        if found is None or found.group(1) != expected:
            raise Refusal("expand", found.group(1) if found else text.strip())
        return found.group(2).split(",") if found.group(2) else []

    def check_options(self, request: Request, allowed: set[str]) -> None:
        for name in request.query_params:
            if name == "$apply":
                raise Refusal("apply")
            if name.startswith("$") and name not in allowed:
                raise Refusal("option", name)

    def listing(self, request: Request, rows: list, fields: dict):
        params = request.query_params
        query = ListQuery(params.get("$filter"), None, params.get("$orderby"), params.get("$top"), params.get("$skip"), params.get("$count"))
        try:
            return apply_list_query(rows, query, fields)
        except InvalidQuery as error:
            token = (params.get("$filter") if error.target == "$filter" else params.get("$orderby") or "").split(" ")[0]
            raise Refusal("parse" if error.target in ("$filter", "$orderby") else "value", token or error.target) from error

    def context(self, entity: str, select: list[str] | None, expand: list[str] | None, nav: str) -> str:
        parts = list(select or [])
        if expand is not None:
            parts.append(nav + (f"({','.join(expand)})" if expand else ""))
        return "$metadata#" + entity + (f"({','.join(parts)})" if parts else "")

    def list_body(self, context: str, rows: list, total: int | None) -> dict:
        body = {"@odata.context": context, "@odata.metadataEtag": METADATA_ETAG}
        if total is not None:
            body["@odata.count"] = total
        return body | {"value": rows}

    def entity_body(self, context: str, row: dict) -> dict:
        return {"@odata.context": context + "/$entity", "@odata.metadataEtag": METADATA_ETAG} | row

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
        return self.list_body(self.context(ITEMS, select, None, ""), rows, result.total)

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
        kinds = {
            "parse": (400, "/IWCOR/CX_OD_EXPR_PARSER_ERROR/00505692409C1EE681AE63616A3CC086", f"Invalid token '{short(error.token)}' at position '1'", "Client_Error"),
            "property": (400, "/IWCOR/CX_OD_SELECT_ERROR/00505692409C1ED5A0F4681CA94457B5", f"Property '{short(error.token)}' not found", "Client_Error"),
            "expand": (400, "/IWCOR/CX_OD_EXPAND_ERROR/00505692409C1EE4AAF7CC158E41116A", f"The expand option's expand path contains an invalid property '{short(error.token)}'", "Client_Error"),
            "option": (400, "/IWCOR/CX_OD_URI_SYNTAX_ERROR/005056A509B11ED394EE3572D5B71927", f"Invalid query parameter '{short(error.token)}' is specified", "Client_Error"),
            "value": (400, "/IWCOR/CX_OD_URI_SYNTAX_ERROR/005056A509B11ED39A954214DFB01045", f"Invalid value for system query option '{short(error.token)}'", "Client_Error"),
            "apply": (501, "SADL_GW/001", "$apply aggregate($count) not supported", "Provider_Application_Error"),
            "missing": (404, "/IWBEP/CM_V4S_RUN/000", "Unspecified provider error occurred. See Error Context and Call Stack.", "Provider_Application_Error"),
        }
        status, code, message, category = kinds[error.kind]
        body = {"code": code, "message": message, "@SAP__common.ExceptionCategory": category}
        if error.kind == "property":
            body["details"] = [{"code": "/IWCOR/CX_OD_EXPAND_ERROR/00505692409C1ED680ACB4DB13157E97", "message": "Invalid select option", "@SAP__common.Severity": "error", "@SAP__common.numericSeverity": 4}]
        body["innererror"] = {
            "ErrorDetails": {
                "@SAP__common.Application": {"ComponentId": "MM-PUR-REQ", "ServiceRepository": "SRVD_A2X", "ServiceId": "API_PURCHASEREQUISITION_2", "ServiceVersion": "0001"},
                "@SAP__common.TransactionId": uuid.uuid4().hex.upper(),
                "@SAP__common.Timestamp": stamp(),
                "@SAP__common.ErrorResolution": {
                    "Analysis": 'Use ADT feed reader "SAP Gateway Error Log" or run transaction /IWFND/ERROR_LOG on SAP Gateway hub system and search for entries with the timestamp above for more details',
                    "Note": "See SAP Note 1797736 for error analysis (https://service.sap.com/sap/support/notes/1797736)",
                },
            }
        }
        return status, {"error": body}


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
