import inspect
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from functools import wraps

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from butterfly.application.alpha import external
from butterfly.application.filter.fields import STANDARD_PURCHASE_ORDER_FIELDS, STANDARD_PURCHASE_ORDER_ITEM_FIELDS
from butterfly.application.filter.parser import parse_filter
from butterfly.domain.entities.purchase_order import PurchaseOrder, PurchaseOrderItem
from butterfly.application.usecase.create_purchase_order import CreatePurchaseOrder
from butterfly.application.usecase.create_sales_order import utc_now
from butterfly.application.usecase.delete_purchase_order_item import DeletePurchaseOrderItem, PurchaseOrderNotFound
from butterfly.domain.errors import ETagMismatch, ETagRequired, InvalidQuery, NumberRangeFull, ValidationDetail, ValidationFailed
from butterfly.domain.repositories.master_data_repo import MasterDataRepo
from butterfly.domain.repositories.purchase_requisition_repo import PurchaseRequisitionRepo
from butterfly.domain.repositories.purchase_order_repo import PurchaseOrderRepo
from butterfly.infrastructure.api.standard import v4
from butterfly.infrastructure.api.standard.dialects import V4_MEDIA, Refusal
from butterfly.infrastructure.api.standard.edmx import PURCHASE_ORDER_METADATA, EntityType, load
from butterfly.infrastructure.api.standard.requisition import EXPAND, LIST_OPTIONS, failure

ROOT = "/sap/opu/odata4/sap/api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001"
METADATA_ETAG = 'W/"20261018074617"'
HEADERS, ITEMS, LINES = "PurchaseOrder", "PurchaseOrderItem", "PurchaseOrderScheduleLine"
ITEMS_OF_HEADER, HEADER_OF_ITEM, LINES_OF_ITEM = "_PurchaseOrderItem", "_PurchaseOrder", "_PurchaseOrderScheduleLineTP"
HEADER_KEYS = ("PurchaseOrder",)
ITEM_KEYS = ("PurchaseOrder", "PurchaseOrderItem")
LINE_KEYS = ("PurchaseOrder", "PurchaseOrderItem", "ScheduleLine")
NUMBER_STRINGS = {"PurchaseRequisitionItem", "PurchaseContractItem", "ReferenceDocumentItem"}
CANCELLED_CODE = "L"


@dataclass(frozen=True)
class HeaderRow:
    purchase_order: str
    order_type: str
    created_by_user: str
    creation_date: date
    order_date: date
    company_code: str
    purchasing_organization: str
    purchasing_group: str
    supplier: str
    document_currency: str
    changed: datetime
    cancelled: bool


@dataclass(frozen=True)
class ItemRow:
    purchase_order: str
    purchase_order_item: str
    material: str
    description: str
    plant: str
    company_code: str
    document_currency: str
    order_quantity: Decimal
    delivered_quantity: Decimal
    unit: str
    net_amount: Decimal
    deletion_code: str
    purchase_requisition: str
    purchase_requisition_item: str
    delivery_date: date
    order_date: date


def header_row_of(order: PurchaseOrder) -> HeaderRow:
    live = [item for item in order.items if not item.is_cancelled]
    first = order.items[0].delivery
    return HeaderRow(
        order.purchase_order, order.order_type, order.created_by_user, order.creation_date_time.date(), first.order_date, order.company_code,
        order.purchasing_organization, order.purchasing_group, external(order.supplier), order.document_currency, order.last_change_date_time, not live,
    )


def item_row_of(order: PurchaseOrder, item: PurchaseOrderItem) -> ItemRow:
    d = item.delivery
    return ItemRow(
        order.purchase_order, external(d.purchase_order_item), d.material, d.material_description or "", item.plant, d.company_code, d.transaction_currency,
        d.ordered_quantity, d.delivered_quantity, d.quantity_unit, d.net_amount, CANCELLED_CODE if item.is_cancelled else "", item.purchase_requisition,
        external(item.purchase_requisition_item) if item.purchase_requisition_item else "", d.promised_delivery_date, d.order_date,
    )


def item_rows(order: PurchaseOrder) -> list[ItemRow]:
    return [item_row_of(order, item) for item in order.items]


def stamp(value: datetime) -> str:
    moment = value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    return moment.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def row_of(entity_type: EntityType, values: dict, select: list[str] | None, keys: tuple[str, ...]) -> dict:
    row = v4.row_of(entity_type, values, "", select, keys, frozenset(NUMBER_STRINGS))
    row.pop("@odata.etag")
    return row


class Service:
    def __init__(self, repo: PurchaseOrderRepo):
        self.repo = repo
        self.metadata = load(PURCHASE_ORDER_METADATA)
        self.header_type = self.metadata.types["PurchaseOrder_Type"]
        self.item_type = self.metadata.types["PurchaseOrderItem_Type"]
        self.line_type = self.metadata.types["PurchaseOrderScheduleLine_Type"]

    def header_values(self, row: HeaderRow) -> dict:
        return {
            "PurchaseOrder": row.purchase_order,
            "PurchaseOrderType": row.order_type,
            "CreatedByUser": row.created_by_user,
            "CreationDate": row.creation_date.isoformat(),
            "PurchaseOrderDate": row.order_date.isoformat(),
            "LastChangeDateTime": stamp(row.changed),
            "PurchaseOrderDeletionCode": CANCELLED_CODE if row.cancelled else "",
            "ReleaseIsNotCompleted": False,
            "CompanyCode": row.company_code,
            "PurchasingOrganization": row.purchasing_organization,
            "PurchasingGroup": row.purchasing_group,
            "Supplier": row.supplier,
            "DocumentCurrency": row.document_currency,
            "ExchangeRate": 1.0,
        }

    def item_values(self, row: ItemRow) -> dict:
        price = (row.net_amount / row.order_quantity) if row.order_quantity else Decimal(0)
        return {
            "PurchaseOrder": row.purchase_order,
            "PurchaseOrderItem": row.purchase_order_item,
            "PurchasingDocumentDeletionCode": row.deletion_code,
            "PurchaseOrderItemText": row.description,
            "Material": row.material,
            "Plant": row.plant,
            "CompanyCode": row.company_code,
            "DocumentCurrency": row.document_currency,
            "OrderQuantity": float(row.order_quantity),
            "PurchaseOrderQuantityUnit": row.unit,
            "BaseUnit": row.unit,
            "OrderPriceUnit": row.unit,
            "NetPriceQuantity": 1,
            "NetPriceAmount": float(price.quantize(Decimal("0.01"))),
            "NetAmount": float(row.net_amount),
            "GrossAmount": float(row.net_amount),
            "EffectiveAmount": float(row.net_amount),
            "PurchaseRequisition": row.purchase_requisition,
            "PurchaseRequisitionItem": row.purchase_requisition_item or "0",
            "GoodsReceiptIsExpected": True,
            "InvoiceIsExpected": True,
        }

    def line_values(self, row: ItemRow) -> dict:
        open_quantity = Decimal(0) if row.deletion_code else row.order_quantity - row.delivered_quantity
        return {
            "PurchaseOrder": row.purchase_order,
            "PurchaseOrderItem": row.purchase_order_item,
            "ScheduleLine": "1",
            "ScheduleLineDeliveryDate": row.delivery_date.isoformat(),
            "ScheduleLineOrderDate": row.order_date.isoformat(),
            "ScheduleLineOrderQuantity": float(row.order_quantity),
            "OpenPurchaseOrderQuantity": float(open_quantity),
            "PurchaseOrderQuantityUnit": row.unit,
            "Currency": row.document_currency,
            "PurchaseRequisition": row.purchase_requisition,
            "PurchaseRequisitionItem": row.purchase_requisition_item or "0",
        }

    def item_row(self, row: ItemRow, select: list[str] | None, header: HeaderRow | None = None) -> dict:
        result = row_of(self.item_type, self.item_values(row), select, ITEM_KEYS)
        if header is not None:
            result[HEADER_OF_ITEM] = self.header_row(header, None, None, [])
        return result

    def line_row(self, row: ItemRow, select: list[str] | None) -> dict:
        return row_of(self.line_type, self.line_values(row), select, LINE_KEYS)

    def header_row(self, row: HeaderRow, select: list[str] | None, expand: list[str] | None, items: list[ItemRow]) -> dict:
        result = row_of(self.header_type, self.header_values(row), select, HEADER_KEYS)
        if expand is not None:
            result[ITEMS_OF_HEADER] = [self.item_row(item, expand or None) for item in items]
        return result

    def expansion(self, text: str | None, expected: str) -> list[str] | None:
        if text is None:
            return None
        found = EXPAND.fullmatch(text.strip())
        if found is None or found.group(1) != expected:
            raise Refusal("expand", found.group(1) if found else text.strip())
        return found.group(2).split(",") if found.group(2) else []

    def context(self, entity: str, select: list[str] | None, expand: list[str] | None, nav: str) -> str:
        keys = {HEADERS: HEADER_KEYS, ITEMS: ITEM_KEYS, LINES: LINE_KEYS}[entity]
        return v4.context(entity, select, expand, nav if expand is not None else "", keys, ITEM_KEYS if entity == HEADERS else HEADER_KEYS)

    def find(self, key: str) -> PurchaseOrder:
        order = self.repo.get(key)
        if order is None:
            raise Refusal("missing")
        return order

    def pairs(self) -> list[tuple[HeaderRow, ItemRow]]:
        return [(header_row_of(order), row) for order in self.repo.list_all() for row in item_rows(order)]

    def header_list(self, request: Request) -> dict:
        v4.check_options(request, LIST_OPTIONS)
        select = v4.selection(request.query_params.get("$select"), self.header_type)
        expand = self.expansion(request.query_params.get("$expand"), ITEMS_OF_HEADER)
        orders = {header_row_of(order): order for order in self.repo.list_all()}
        result = v4.listing(request, list(orders), STANDARD_PURCHASE_ORDER_FIELDS)
        rows = [self.header_row(row, select, expand, item_rows(orders[row])) for row in result.rows]
        return v4.list_body(self.context(HEADERS, select, expand, ITEMS_OF_HEADER), rows, result.total, METADATA_ETAG)

    def header_entity(self, request: Request, key: str) -> dict:
        v4.check_options(request, {"$select", "$expand", "$format"})
        select = v4.selection(request.query_params.get("$select"), self.header_type)
        expand = self.expansion(request.query_params.get("$expand"), ITEMS_OF_HEADER)
        order = self.find(key)
        row = self.header_row(header_row_of(order), select, expand, item_rows(order))
        return v4.entity_body(self.context(HEADERS, select, expand, ITEMS_OF_HEADER), row, METADATA_ETAG)

    def items_of_header(self, request: Request, key: str) -> dict:
        v4.check_options(request, LIST_OPTIONS)
        select = v4.selection(request.query_params.get("$select"), self.item_type)
        result = v4.listing(request, item_rows(self.find(key)), STANDARD_PURCHASE_ORDER_ITEM_FIELDS)
        return v4.list_body(f"$metadata#{ITEMS}", [self.item_row(row, select) for row in result.rows], result.total, METADATA_ETAG)

    def item_list(self, request: Request) -> dict:
        v4.check_options(request, LIST_OPTIONS)
        select = v4.selection(request.query_params.get("$select"), self.item_type)
        expand = self.expansion(request.query_params.get("$expand"), HEADER_OF_ITEM)
        headers = {row.purchase_order: header for header, row in self.pairs()}
        result = v4.listing(request, [row for _, row in self.pairs()], STANDARD_PURCHASE_ORDER_ITEM_FIELDS)
        rows = [self.item_row(row, select, headers[row.purchase_order] if expand is not None else None) for row in result.rows]
        return v4.list_body(self.context(ITEMS, select, expand, HEADER_OF_ITEM), rows, result.total, METADATA_ETAG)

    def found_item(self, key: str, item_key: str) -> ItemRow:
        for row in item_rows(self.find(key)):
            if row.purchase_order_item == external(item_key):
                return row
        raise Refusal("missing")

    def item_entity(self, request: Request, key: str, item_key: str) -> dict:
        v4.check_options(request, {"$select", "$format"})
        select = v4.selection(request.query_params.get("$select"), self.item_type)
        row = self.found_item(key, item_key)
        return v4.entity_body(self.context(ITEMS, select, None, ""), self.item_row(row, select), METADATA_ETAG)

    def line_list(self, request: Request) -> dict:
        v4.check_options(request, LIST_OPTIONS)
        select = v4.selection(request.query_params.get("$select"), self.line_type)
        result = v4.listing(request, [row for _, row in self.pairs()], STANDARD_PURCHASE_ORDER_ITEM_FIELDS)
        return v4.list_body(self.context(LINES, select, None, ""), [self.line_row(row, select) for row in result.rows], result.total, METADATA_ETAG)

    def lines_of_item(self, request: Request, key: str, item_key: str) -> dict:
        v4.check_options(request, LIST_OPTIONS)
        select = v4.selection(request.query_params.get("$select"), self.line_type)
        row = self.found_item(key, item_key)
        return v4.list_body(f"$metadata#{LINES}", [self.line_row(row, select)], None, METADATA_ETAG)

    def count(self, request: Request, items: bool) -> Response:
        text = request.query_params.get("$filter")
        fields = STANDARD_PURCHASE_ORDER_ITEM_FIELDS if items else STANDARD_PURCHASE_ORDER_FIELDS
        try:
            condition = None if text is None else parse_filter(text, fields)
        except InvalidQuery as error:
            raise Refusal("parse", text.split(" ")[0]) from error
        rows = [row for _, row in self.pairs()] if items else [header_row_of(order) for order in self.repo.list_all()]
        return Response(str(len([row for row in rows if condition is None or condition.matches(row)])), media_type="text/plain; charset=utf-8")

    def refusal(self, error: Refusal) -> tuple[int, dict]:
        return v4.refusal_response(error, "MM-PUR-PO", "API_PURCHASEORDER_2")


def build_purchase_order_router(
    repo: PurchaseOrderRepo, requisitions: PurchaseRequisitionRepo, master_data: MasterDataRepo, now: Callable[[], datetime] = utc_now
) -> APIRouter:
    service = Service(repo)
    created: dict[str, str] = {}
    router = APIRouter(prefix=ROOT)

    def answer(outcome):
        return outcome if isinstance(outcome, Response) else JSONResponse(outcome, media_type=V4_MEDIA)

    def refused(error: Exception):
        if isinstance(error, Refusal):
            status, body = service.refusal(error)
        elif isinstance(error, ValidationFailed):
            details = [{"code": d.code, "message": d.message, "target": d.target} for d in error.details]
            status, body = failure(400, "VALIDATION_FAILED", "The purchase order has errors.", details=details)
        elif isinstance(error, ETagRequired):
            status, body = failure(428, "ETAG_REQUIRED", "An If-Match header with the etag from the last read is required.")
        elif isinstance(error, ETagMismatch):
            status, body = failure(412, "ETAG_MISMATCH", "The purchase order was changed by someone else. Reload and try again.")
        elif isinstance(error, PurchaseOrderNotFound):
            status, body = service.refusal(Refusal("missing"))
        else:
            status, body = failure(400, "NUMBER_RANGE_FULL", "The purchase order number range is full.")
        return JSONResponse(body, status_code=status, media_type=V4_MEDIA)

    caught = (Refusal, ValidationFailed, NumberRangeFull, ETagRequired, ETagMismatch, PurchaseOrderNotFound)

    def guarded(function: Callable):
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
        return with_etag(service.header_entity(request, key), service.find(key))

    @router.get(f"/{HEADERS}(" + "'{key}')/" + ITEMS_OF_HEADER)
    @guarded
    def header_items(request: Request, key: str):
        return service.items_of_header(request, key)

    @router.get(f"/{ITEMS}")
    @guarded
    def items(request: Request):
        return service.item_list(request)

    @router.get(f"/{ITEMS}(PurchaseOrder='" + "{key}',PurchaseOrderItem='{item_key}')")
    @guarded
    def item(request: Request, key: str, item_key: str):
        return with_etag(service.item_entity(request, key, item_key), service.find(key))

    @router.patch(f"/{ITEMS}(PurchaseOrder='" + "{key}',PurchaseOrderItem='{item_key}')")
    @guarded
    async def change(request: Request, key: str, item_key: str):
        use_case = DeletePurchaseOrderItem(repo, requisitions, now)
        order = use_case.execute(key, item_key, request.headers.get("if-match"), await json_body(request))
        return with_etag(service.item_entity(request, key, item_key), order)

    @router.get(f"/{ITEMS}(PurchaseOrder='" + "{key}',PurchaseOrderItem='{item_key}')/" + LINES_OF_ITEM)
    @guarded
    def item_lines(request: Request, key: str, item_key: str):
        return service.lines_of_item(request, key, item_key)

    @router.get(f"/{LINES}")
    @guarded
    def lines(request: Request):
        return service.line_list(request)

    def with_etag(body: dict, order: PurchaseOrder) -> JSONResponse:
        return JSONResponse(body, headers={"ETag": order.etag}, media_type=V4_MEDIA)

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
        key = request.headers.get("idempotency-key")
        order = repo.get(created[key]) if key in created else None
        if order is None:
            order = CreatePurchaseOrder(repo, requisitions, master_data, now).execute(await json_body(request))
            if key:
                created[key] = order.purchase_order
        row = service.header_row(header_row_of(order), None, [], item_rows(order))
        location = f"{str(request.base_url).rstrip('/')}{ROOT}/{HEADERS}('{order.purchase_order}')"
        body = v4.entity_body(service.context(HEADERS, None, [], ITEMS_OF_HEADER), row, METADATA_ETAG)
        return JSONResponse(body, status_code=201, headers={"Location": location}, media_type=V4_MEDIA)

    def add_empty(name: str):
        @router.get(f"/{name}")
        @guarded
        def empty(request: Request):
            return v4.list_body(f"$metadata#{name}", [], None, METADATA_ETAG)

    for name in service.metadata.sets:
        if name not in (HEADERS, ITEMS, LINES):
            add_empty(name)

    return router
