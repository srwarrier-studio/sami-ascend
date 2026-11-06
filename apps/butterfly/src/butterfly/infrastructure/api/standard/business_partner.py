import re
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, Response

from butterfly.application.alpha import external
from butterfly.application.dto.list_query_dto import ListQuery
from butterfly.application.filter import fields as filter_fields
from butterfly.application.filter.parser import parse_filter
from butterfly.application.list_query import apply_list_query
from butterfly.domain.entities.master_data import DEFAULT_PURCHASING_GROUP, PURCHASING_ORGANIZATIONS, SALES_ORGANIZATIONS
from butterfly.domain.errors import InvalidQuery
from butterfly.domain.repositories.master_data_repo import MasterDataRepo
from butterfly.infrastructure.api.standard.dialects import V2_MEDIA, Refusal, stamp
from butterfly.infrastructure.api.standard.edmx import PARTNER_METADATA, load

ROOT = "/sap/opu/odata/sap/API_BUSINESS_PARTNER"
SERVICE = "API_BUSINESS_PARTNER"
LIST_OPTIONS = {"$filter", "$select", "$orderby", "$top", "$skip", "$inlinecount", "$expand", "$format"}
SUBSTRINGOF = re.compile(r"substringof\(\s*('(?:[^']|'')*')\s*,\s*(\w+)\s*\)")
CUSTOMER_GROUP, SUPPLIER_GROUP = "CUST", "SUPL"


@dataclass(frozen=True)
class CustomerRow:
    customer: str
    name: str
    account_group: str = CUSTOMER_GROUP


@dataclass(frozen=True)
class CustomerCompanyRow:
    customer: str
    company_code: str
    account_group: str = CUSTOMER_GROUP


@dataclass(frozen=True)
class CustomerSalesAreaRow:
    customer: str
    sales_organization: str
    distribution_channel: str = "10"
    division: str = "00"
    account_group: str = CUSTOMER_GROUP


@dataclass(frozen=True)
class SupplierRow:
    supplier: str
    name: str
    account_group: str = SUPPLIER_GROUP


@dataclass(frozen=True)
class SupplierCompanyRow:
    supplier: str
    company_code: str
    account_group: str = SUPPLIER_GROUP


@dataclass(frozen=True)
class SupplierPurchasingOrgRow:
    supplier: str
    purchasing_organization: str
    purchasing_group: str = DEFAULT_PURCHASING_GROUP
    account_group: str = SUPPLIER_GROUP


@dataclass(frozen=True)
class EntitySet:
    name: str
    type_name: str
    keys: tuple[str, ...]
    fields: dict
    rows: Callable[[], list]
    values: Callable[[object], dict]
    children: dict[str, str]
    parent_attribute: str


def blank(edm: str):
    if edm == "Edm.String":
        return ""
    if edm == "Edm.Boolean":
        return False
    if edm == "Edm.Decimal":
        return "0"
    return None


def rewrite_substringof(text: str | None) -> str | None:
    return None if text is None else SUBSTRINGOF.sub(lambda m: f"contains({m.group(2)},{m.group(1)})", text)


class Service:
    def __init__(self, master_data: MasterDataRepo):
        self.master_data = master_data
        self.metadata = load(PARTNER_METADATA)
        self.sets = {s.name: s for s in self.build_sets()}

    def build_sets(self) -> list[EntitySet]:
        f = filter_fields
        name = lambda r: {"CustomerName": r.name, "CustomerFullName": r.name, "BPCustomerName": r.name, "BPCustomerFullName": r.name}  # noqa: E731
        return [
            EntitySet(
                "A_Customer", "A_CustomerType", ("Customer",), f.STANDARD_CUSTOMER_FIELDS, self.customers,
                lambda r: {"Customer": external(r.customer), "CustomerAccountGroup": r.account_group} | name(r),
                {"to_CustomerCompany": "A_CustomerCompany", "to_CustomerSalesArea": "A_CustomerSalesArea"}, "customer",
            ),
            EntitySet(
                "A_CustomerCompany", "A_CustomerCompanyType", ("Customer", "CompanyCode"), f.STANDARD_CUSTOMER_COMPANY_FIELDS, self.customer_companies,
                lambda r: {"Customer": external(r.customer), "CompanyCode": r.company_code, "CustomerAccountGroup": r.account_group}, {}, "customer",
            ),
            EntitySet(
                "A_CustomerSalesArea", "A_CustomerSalesAreaType", ("Customer", "SalesOrganization", "DistributionChannel", "Division"),
                f.STANDARD_CUSTOMER_SALES_AREA_FIELDS, self.customer_sales_areas,
                lambda r: {
                    "Customer": external(r.customer), "SalesOrganization": r.sales_organization, "DistributionChannel": r.distribution_channel,
                    "Division": r.division, "CustomerAccountGroup": r.account_group,
                },
                {}, "customer",
            ),
            EntitySet(
                "A_Supplier", "A_SupplierType", ("Supplier",), f.STANDARD_SUPPLIER_FIELDS, self.suppliers,
                lambda r: {"Supplier": external(r.supplier), "SupplierName": r.name, "SupplierFullName": r.name, "SupplierAccountGroup": r.account_group},
                {"to_SupplierCompany": "A_SupplierCompany", "to_SupplierPurchasingOrg": "A_SupplierPurchasingOrg"}, "supplier",
            ),
            EntitySet(
                "A_SupplierCompany", "A_SupplierCompanyType", ("Supplier", "CompanyCode"), f.STANDARD_SUPPLIER_COMPANY_FIELDS, self.supplier_companies,
                lambda r: {"Supplier": external(r.supplier), "CompanyCode": r.company_code, "SupplierAccountGroup": r.account_group}, {}, "supplier",
            ),
            EntitySet(
                "A_SupplierPurchasingOrg", "A_SupplierPurchasingOrgType", ("Supplier", "PurchasingOrganization"),
                f.STANDARD_SUPPLIER_PURCHASING_ORG_FIELDS, self.supplier_purchasing_orgs,
                lambda r: {
                    "Supplier": external(r.supplier), "PurchasingOrganization": r.purchasing_organization, "PurchasingGroup": r.purchasing_group,
                    "SupplierAccountGroup": r.account_group,
                },
                {}, "supplier",
            ),
        ]

    def customers(self) -> list[CustomerRow]:
        return [CustomerRow(c.customer_id, c.name) for c in self.master_data.list_customers()]

    def customer_companies(self) -> list[CustomerCompanyRow]:
        return [CustomerCompanyRow(c.customer_id, c.company_code) for c in self.master_data.list_customers()]

    def customer_sales_areas(self) -> list[CustomerSalesAreaRow]:
        return [CustomerSalesAreaRow(c.customer_id, SALES_ORGANIZATIONS[c.company_code]) for c in self.master_data.list_customers()]

    def suppliers(self) -> list[SupplierRow]:
        return [SupplierRow(s.supplier_id, s.name) for s in self.master_data.list_suppliers()]

    def supplier_companies(self) -> list[SupplierCompanyRow]:
        return [SupplierCompanyRow(s.supplier_id, s.company_code) for s in self.master_data.list_suppliers()]

    def supplier_purchasing_orgs(self) -> list[SupplierPurchasingOrgRow]:
        return [SupplierPurchasingOrgRow(s.supplier_id, PURCHASING_ORGANIZATIONS[s.company_code]) for s in self.master_data.list_suppliers()]

    def key_text(self, entity: EntitySet, source) -> str:
        values = entity.values(source)
        if len(entity.keys) == 1:
            return f"'{values[entity.keys[0]]}'"
        return ",".join(f"{key}='{values[key]}'" for key in entity.keys)

    def row(self, entity: EntitySet, source, select: list[str] | None, expand: str | None, base: str) -> dict:
        entity_type = self.metadata.types[entity.type_name]
        row = {name: blank(edm) for name, edm in entity_type.properties}
        row |= {name: value for name, value in entity.values(source).items() if name in row}
        uri = f"{base}{ROOT}/{entity.name}({self.key_text(entity, source)})"
        meta = {"id": uri, "uri": uri, "type": f"{SERVICE}.{entity.type_name}"}
        if select is not None:
            row = {name: row[name] for name, _ in entity_type.properties if name in select}
            links = {}
        else:
            links = {nav: {"__deferred": {"uri": f"{uri}/{nav}"}} for nav in entity_type.navigation}
        if expand is not None and (select is None or expand in {name.split("/")[0] for name in select}):
            child = self.sets[entity.children[expand]]
            parent_value = getattr(source, entity.parent_attribute)
            links[expand] = {"results": [self.row(child, r, None, None, base) for r in child.rows() if getattr(r, entity.parent_attribute) == parent_value]}
        return {"__metadata": meta} | row | links

    def selection(self, text: str | None, entity: EntitySet) -> list[str] | None:
        if text is None:
            return None
        names = [name.strip() for name in text.split(",")]
        entity_type = self.metadata.types[entity.type_name]
        for name in names:
            if name not in entity_type.names() and name.split("/")[0] not in entity_type.navigation:
                raise Refusal("segment", name)
        return names

    def expansion(self, text: str | None, entity: EntitySet) -> str | None:
        if text is None:
            return None
        name = text.strip()
        if name not in entity.children:
            raise Refusal("segment", name)
        return name

    def check_options(self, request: Request, allowed: set[str]) -> None:
        for name in request.query_params:
            if name.startswith("$") and name not in allowed:
                raise Refusal("option", name)

    def listing(self, request: Request, entity: EntitySet, rows: list):
        params = request.query_params
        text = rewrite_substringof(params.get("$filter"))
        query = ListQuery(text, None, params.get("$orderby"), params.get("$top"), params.get("$skip"), "true" if params.get("$inlinecount") == "allpages" else None)
        try:
            return apply_list_query(rows, query, entity.fields)
        except InvalidQuery as error:
            if error.target in ("$filter", "$orderby"):
                raise Refusal("property", (text if error.target == "$filter" else params.get("$orderby") or "").split(" ")[0].split("(")[0], entity.type_name) from error
            raise Refusal("value", error.target) from error

    def list_of(self, request: Request, entity: EntitySet, rows: list | None = None) -> dict:
        self.check_options(request, LIST_OPTIONS)
        select = self.selection(request.query_params.get("$select"), entity)
        expand = self.expansion(request.query_params.get("$expand"), entity)
        result = self.listing(request, entity, entity.rows() if rows is None else rows)
        base = str(request.base_url).rstrip("/")
        rows = [self.row(entity, r, select, expand, base) for r in result.rows]
        return {"d": ({"__count": str(result.total)} if result.total is not None else {}) | {"results": rows}}

    def entity_of(self, request: Request, entity: EntitySet, keys: list[str]) -> dict:
        self.check_options(request, {"$select", "$expand", "$format"})
        select = self.selection(request.query_params.get("$select"), entity)
        expand = self.expansion(request.query_params.get("$expand"), entity)
        wanted = tuple(external(key) for key in keys)
        found = next((r for r in entity.rows() if tuple(external(entity.values(r)[k]) for k in entity.keys) == wanted), None)
        if found is None:
            raise Refusal("missing", type_name=entity.type_name)
        return {"d": self.row(entity, found, select, expand, str(request.base_url).rstrip("/"))}

    def children_of(self, request: Request, entity: EntitySet, key: str, nav: str) -> dict:
        found = next((r for r in entity.rows() if external(entity.values(r)[entity.keys[0]]) == external(key)), None)
        if found is None:
            raise Refusal("missing", type_name=entity.type_name)
        child = self.sets[entity.children[nav]]
        parent_value = getattr(found, entity.parent_attribute)
        return self.list_of(request, child, [r for r in child.rows() if getattr(r, entity.parent_attribute) == parent_value])

    def count(self, request: Request, entity: EntitySet) -> Response:
        text = rewrite_substringof(request.query_params.get("$filter"))
        try:
            condition = None if text is None else parse_filter(text, entity.fields)
        except InvalidQuery as error:
            raise Refusal("property", text.split(" ")[0].split("(")[0], entity.type_name) from error
        return Response(str(len([r for r in entity.rows() if condition is None or condition.matches(r)])), media_type="text/plain; charset=utf-8")

    def refusal(self, error: Refusal) -> tuple[int, dict]:
        type_name = error.type_name
        kinds = {
            "property": (400, "005056A509B11EE1B9A8FEA8DE87F78E", f"Property {error.token} not found in type {type_name}"),
            "segment": (404, "005056A509B11EE1B9A8FEC11C21D78E", f"Resource not found for the segment '{error.token}'."),
            "option": (400, "00505692409C1ED98BC626766B3596A5", "Invalid system query option specified"),
            "value": (400, "005056A509B11EE1B9A8FEC11C22F78E", "Invalid system query options value"),
            "missing": (404, "/IWBEP/CM_MGW_RT/020", f"Resource not found for segment '{type_name}'"),
        }
        status, code, message = kinds[error.kind]
        inner = {"transactionid": uuid.uuid4().hex.upper(), "timestamp": stamp() + "0"}
        if error.kind == "missing":
            inner = {"application": {"component_id": "LO-MD-BP", "service_namespace": "/SAP/", "service_id": SERVICE, "service_version": "0001"}} | inner
        inner["Error_Resolution"] = {
            "SAP_Transaction": 'For backend administrators: use ADT feed reader "SAP Gateway Error Log" or run transaction /IWFND/ERROR_LOG on SAP Gateway hub system and search for entries with the timestamp above for more details',
            "SAP_Note": "See SAP Note 1797736 for error analysis (https://service.sap.com/sap/support/notes/1797736)",
        }
        if error.kind == "missing":
            link = f"/sap/opu/odata/iwbep/message_text;o=LOCAL/T100_longtexts(MSGID='%2FIWBEP%2FCM_MGW_RT',MSGNO='020',MESSAGE_V1='{type_name}',MESSAGE_V2='',MESSAGE_V3='',MESSAGE_V4='')/$value"
            inner["longtext_url"] = link
            inner["errordetails"] = [
                {"ContentID": "", "code": "/IWBEP/CX_MGW_BUSI_EXCEPTION", "message": message, "longtext_url": link, "propertyref": "", "severity": "error", "transition": False, "target": ""}
            ]
        return status, {"error": {"code": code, "message": {"lang": "en", "value": message}, "innererror": inner}}


def build_business_partner_router(master_data: MasterDataRepo) -> APIRouter:
    service = Service(master_data)
    router = APIRouter(prefix=ROOT)

    def guarded(function):
        @wraps(function)
        def handler(*args, **kwargs):
            try:
                outcome = function(*args, **kwargs)
            except Refusal as error:
                status, body = service.refusal(error)
                return JSONResponse(body, status_code=status, media_type=V2_MEDIA)
            return outcome if isinstance(outcome, Response) else JSONResponse(outcome, media_type=V2_MEDIA)

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

        slots = ",".join(f"{key}='{{k{i}}}'" for i, key in enumerate(entity.keys))
        path = f"/{entity.name}('{{k0}}')" if len(entity.keys) == 1 else f"/{entity.name}({slots})"

        if len(entity.keys) == 1:

            @router.get(path)
            @guarded
            def one(request: Request, k0: str):
                return service.entity_of(request, entity, [k0])

        elif len(entity.keys) == 2:

            @router.get(path)
            @guarded
            def of_two(request: Request, k0: str, k1: str):
                return service.entity_of(request, entity, [k0, k1])

        else:

            @router.get(path)
            @guarded
            def of_four(request: Request, k0: str, k1: str, k2: str, k3: str):
                return service.entity_of(request, entity, [k0, k1, k2, k3])

        for nav in entity.children:

            @router.get(f"/{entity.name}('{{k0}}')/{nav}")
            @guarded
            def children(request: Request, k0: str, nav=nav):
                return service.children_of(request, entity, k0, nav)

    for entity in service.sets.values():
        add_routes(entity)

    def add_empty(name: str):
        @router.get(f"/{name}")
        @guarded
        def empty(request: Request):
            return {"d": {"results": []}}

    for name in service.metadata.sets:
        if name not in service.sets:
            add_empty(name)

    return router
