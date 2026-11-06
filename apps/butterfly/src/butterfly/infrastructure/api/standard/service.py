import re
from collections import defaultdict
from decimal import Decimal
from functools import wraps

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from butterfly.application.alpha import external
from butterfly.application.dto.list_query_dto import ListQuery
from butterfly.application.filter.fields import FieldType
from butterfly.application.filter.parser import parse_filter
from butterfly.application.list_query import apply_list_query
from butterfly.domain.entities.sales_order import SalesOrder
from butterfly.domain.errors import InvalidQuery
from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo
from butterfly.infrastructure.api.standard.dialects import Refusal, item_rows

LIST_OPTIONS = {"$filter", "$select", "$orderby", "$top", "$skip", "$expand"}
AMOUNTS = {"order": "TotalNetAmount", "item": "NetAmount"}
ALIAS = re.compile(r"(\w+) with (\w+) as (\w+)")


def offending(error: InvalidQuery, text: str | None) -> str:
    found = re.search(r"(?:field|operator) '?(\w+)|by '(\w+)", error.message)
    if found:
        return found.group(1) or found.group(2)
    return (text or "").split(" ")[0]


def balanced(text: str, start: int) -> int:
    depth = 0
    for position in range(start, len(text)):
        depth += {"(": 1, ")": -1}.get(text[position], 0)
        if depth == 0:
            return position
    raise Refusal("parse", text[start : start + 4])


class Service:
    def __init__(self, dialect, repo: SalesOrderRepo):
        self.dialect = dialect
        self.repo = repo

    def find(self, key: str) -> SalesOrder:
        order = self.repo.get(key) or self.repo.get(key.zfill(10))
        if order is None:
            raise Refusal("missing")
        return order

    def check_options(self, request: Request, allowed: set[str]) -> None:
        for name in request.query_params:
            extra = {"$apply"} if self.dialect.supports_apply else set()
            if name.startswith("$") and name not in allowed | extra | {self.dialect.count_option, "$format"}:
                raise Refusal("apply" if name == "$apply" else "option", name)

    def selection(self, text: str | None, entity_type) -> list[str] | None:
        if text is None:
            return None
        names = [name.strip() for name in text.split(",")]
        known = entity_type.names()
        for name in names:
            if name not in known:
                raise Refusal("property", name)
        return names

    def filter_text(self, text: str | None, kind: str) -> str | None:
        if text is None:
            return None
        if self.dialect.name == "V2":
            text = re.sub(r"datetime'(\d{4}-\d{2}-\d{2})T00:00:00'", r"\1", text)
            text = re.sub(r"datetime(?:offset)?'(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2})Z?'", r"\1Z", text)
            text = re.sub(r"(\d)[mM]\b", r"\1", text)
        amount = AMOUNTS[kind]
        if self.dialect.name == "V4" and re.search(rf"\b{amount}\b", text) and not re.search(r"\bTransactionCurrency\b", text):
            raise Refusal("currency", amount)
        return text

    def wants_count(self, request: Request) -> bool:
        value = request.query_params.get(self.dialect.count_option)
        return value == ("true" if self.dialect.name == "V4" else "allpages")

    def listing(self, request: Request, source, fields: dict, kind: str):
        params = request.query_params
        text = self.filter_text(params.get("$filter"), kind)
        query = ListQuery(text, None, params.get("$orderby"), params.get("$top"), params.get("$skip"), "true" if self.wants_count(request) else None)
        try:
            return apply_list_query(source, query, fields)
        except InvalidQuery as error:
            token = offending(error, text if error.target == "$filter" else params.get("$orderby"))
            raise Refusal("parse" if error.target in ("$filter", "$orderby") else "option", token) from error

    def matching(self, request: Request, source, fields: dict, kind: str) -> list:
        text = self.filter_text(request.query_params.get("$filter"), kind)
        try:
            condition = None if text is None else parse_filter(text, fields)
        except InvalidQuery as error:
            raise Refusal("parse", offending(error, text)) from error
        rows = source() if callable(source) else source
        return rows if condition is None else [row for row in rows if condition.matches(row)]

    def order_list(self, request: Request):
        self.check_options(request, LIST_OPTIONS)
        d = self.dialect
        if "$apply" in request.query_params:
            return self.apply(request)
        select = self.selection(request.query_params.get("$select"), d.order_type)
        expand = d.expand_options(request.query_params.get("$expand"))
        result = self.listing(request, self.repo.listing(), d.order_fields, "order")
        base = str(request.base_url).rstrip("/")
        rows = [d.order_row(order, select, expand, base) for order in result.rows]
        expand_select = expand[0] if expand else None
        context = d.context(d.order_set, select, expand_select, expand is not None)
        return d.list_body(context, rows, result.total)

    def order_entity(self, request: Request, key: str):
        d = self.dialect
        self.check_options(request, {"$select", "$expand"})
        select = self.selection(request.query_params.get("$select"), d.order_type)
        expand = d.expand_options(request.query_params.get("$expand"))
        order = self.find(key)
        row = d.order_row(order, select, expand, str(request.base_url).rstrip("/"))
        context = d.context(d.order_set, select, expand[0] if expand else None, expand is not None)
        return d.entity_body(context, row)

    def items_of_order(self, request: Request, key: str):
        d = self.dialect
        self.check_options(request, LIST_OPTIONS)
        select = self.selection(request.query_params.get("$select"), d.item_type)
        order = self.find(key)
        result = self.listing(request, item_rows(order), d.item_fields, "item")
        rows = [d.item_row(item, select, str(request.base_url).rstrip("/")) for item in result.rows]
        return d.list_body(f"$metadata#{d.item_set}", rows, result.total)

    def item_list(self, request: Request):
        d = self.dialect
        self.check_options(request, LIST_OPTIONS | {"$apply"})
        if "$apply" in request.query_params:
            return self.apply(request, items=True)
        select = self.selection(request.query_params.get("$select"), d.item_type)
        flat = [item for order in self.repo.list_all() for item in item_rows(order)]
        result = self.listing(request, flat, d.item_fields, "item")
        rows = [d.item_row(item, select, str(request.base_url).rstrip("/")) for item in result.rows]
        return d.list_body(f"$metadata#{d.item_set}", rows, result.total)

    def item_entity(self, request: Request, order_key: str, item_key: str):
        d = self.dialect
        order = self.find(order_key)
        wanted = item_key.lstrip("0") or "0"
        for item in item_rows(order):
            if item.sales_order_item.lstrip("0") == wanted:
                return d.entity_body(f"$metadata#{d.item_set}", d.item_row(item, None, str(request.base_url).rstrip("/")))
        raise Refusal("missing")

    def count(self, request: Request, items: bool = False) -> Response:
        d = self.dialect
        if items:
            rows = self.matching(request, lambda: [i for o in self.repo.list_all() for i in item_rows(o)], d.item_fields, "item")
        else:
            rows = self.matching(request, self.repo.list_all, d.order_fields, "order")
        return Response(str(len(rows)), media_type="text/plain; charset=utf-8")

    def apply(self, request: Request, items: bool = False):
        d = self.dialect
        if not d.supports_apply:
            raise Refusal("apply")
        text = request.query_params["$apply"].strip()
        pipeline = text
        filter_text = None
        if text.startswith("filter("):
            end = balanced(text, len("filter"))
            filter_text = text[len("filter(") : end]
            if text[end + 1 : end + 2] != "/":
                raise Refusal("parse", text)
            pipeline = text[end + 2 :]
        if not pipeline.startswith("groupby(("):
            raise Refusal("parse", pipeline)
        keys_end = pipeline.index(")", len("groupby(("))
        keys = [name.strip() for name in pipeline[len("groupby((") : keys_end].split(",")]
        rest = pipeline[keys_end + 1 :]
        if not rest.startswith(",aggregate(") or not rest.endswith("))"):
            raise Refusal("parse", rest)
        aggregates = []
        for part in rest[len(",aggregate(") : -2].split(","):
            found = ALIAS.fullmatch(part.strip())
            if found is None:
                raise Refusal("parse", part.strip())
            if found.group(2) != "sum":
                raise Refusal("apply")
            aggregates.append(found.groups())
        fields = d.item_fields if items else d.order_fields
        kind = "item" if items else "order"
        amount = AMOUNTS[kind]
        for name in keys:
            if name not in fields:
                raise Refusal("property", name)
        for field_name, _, alias in aggregates:
            if field_name != amount:
                raise Refusal("property", field_name)
        aliases = {alias for _, _, alias in aggregates}
        orderby = request.query_params.get("$orderby")
        if orderby and orderby.split()[0] in aliases:
            raise Refusal("parse", orderby.split()[0])
        if filter_text is not None and d.name == "V4" and re.search(rf"\b{amount}\b", filter_text) and "TransactionCurrency" not in filter_text:
            raise Refusal("currency", amount)
        if filter_text is not None:
            try:
                condition = parse_filter(filter_text, fields)
            except InvalidQuery as error:
                raise Refusal("parse", offending(error, filter_text)) from error
        else:
            condition = None
        rows = [i for o in self.repo.list_all() for i in item_rows(o)] if items else self.repo.list_all()
        if condition is not None:
            rows = [row for row in rows if condition.matches(row)]
        groups: dict[tuple, list[Decimal]] = defaultdict(list)
        for row in rows:
            groups[tuple(getattr(row, fields[name][0]) for name in keys)].append(getattr(row, fields[amount][0]))
        result = []
        for group_key in sorted(groups, key=lambda key: tuple("" if part is None else str(part) for part in key)):
            line = {"@odata.etag": 'W/""'}
            for name, part in zip(keys, group_key):
                line[name] = external(part) if fields[name][1] is FieldType.KEY else part.isoformat() if hasattr(part, "isoformat") else part
            for _, _, alias in aggregates:
                line[alias] = float(sum(groups[group_key], Decimal(0)))
                line[f"{alias}@odata.type"] = "#Decimal"
            result.append(line)
        skip = int(request.query_params.get("$skip", 0))
        top = int(request.query_params.get("$top", 100))
        context = f"$metadata#{d.item_set if items else d.order_set}({','.join(keys + [a for _, _, a in aggregates])})"
        total = len(result) if self.wants_count(request) else None
        return d.list_body(context, result[skip : skip + top], total)


def build_router(dialect, repo: SalesOrderRepo) -> APIRouter:
    service = Service(dialect, repo)
    router = APIRouter(prefix=dialect.root)

    def guarded(function):
        @wraps(function)
        def handler(*args, **kwargs):
            try:
                result = function(*args, **kwargs)
            except Refusal as error:
                status, body = dialect.refusal(error)
                return JSONResponse(body, status_code=status, media_type=dialect.media)
            return result if isinstance(result, Response) else JSONResponse(result, media_type=dialect.media)

        return handler

    order_set, item_set, nav = dialect.order_set, dialect.item_set, dialect.nav

    @router.get("/$metadata")
    def metadata():
        return Response(dialect.metadata.content(), media_type="application/xml")

    @router.get(f"/{order_set}/$count")
    @guarded
    def order_count(request: Request):
        return service.count(request)

    @router.get(f"/{item_set}/$count")
    @guarded
    def item_count(request: Request):
        return service.count(request, items=True)

    @router.get(f"/{order_set}")
    @guarded
    def orders(request: Request):
        return service.order_list(request)

    @router.get(f"/{order_set}(" + "'{key}')")
    @guarded
    def order(request: Request, key: str):
        return service.order_entity(request, key)

    @router.get(f"/{order_set}(" + "'{key}')/" + nav)
    @guarded
    def order_items(request: Request, key: str):
        return service.items_of_order(request, key)

    @router.get(f"/{item_set}")
    @guarded
    def items(request: Request):
        return service.item_list(request)

    @router.get(f"/{item_set}(SalesOrder='" + "{order_key}',SalesOrderItem='{item_key}')")
    @guarded
    def item(request: Request, order_key: str, item_key: str):
        return service.item_entity(request, order_key, item_key)

    def add_empty(name: str):
        @router.get(f"/{name}")
        @guarded
        def empty(request: Request):
            return dialect.list_body(f"$metadata#{name}", [], None)

    for name in dialect.metadata.sets:
        if name not in (order_set, item_set):
            add_empty(name)

    return router
