import uuid

from fastapi import Request

from butterfly.application.dto.list_query_dto import ListQuery
from butterfly.application.list_query import apply_list_query
from butterfly.domain.errors import InvalidQuery
from butterfly.infrastructure.api.standard.dialects import Refusal, short, stamp
from butterfly.infrastructure.api.standard.edmx import EntityType

RESOLUTION = {
    "Analysis": 'Use ADT feed reader "SAP Gateway Error Log" or run transaction /IWFND/ERROR_LOG on SAP Gateway hub system and search for entries with the timestamp above for more details',
    "Note": "See SAP Note 1797736 for error analysis (https://service.sap.com/sap/support/notes/1797736)",
}


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


def row_of(entity_type: EntityType, values: dict, etag: str, select: list[str] | None, keys: tuple[str, ...], zero_strings: frozenset[str] = frozenset()) -> dict:
    row = {name: blank(edm) for name, edm in entity_type.properties}
    row |= {name: "0" for name in zero_strings & row.keys()}
    row |= {name: value for name, value in values.items() if name in row}
    names = None if select is None else [name for name, _ in entity_type.properties if name in select or name in keys]
    return {"@odata.etag": etag} | (row if names is None else {name: row[name] for name in names})


def selection(text: str | None, entity_type: EntityType) -> list[str] | None:
    if text is None:
        return None
    names = [name.strip() for name in text.split(",")]
    for name in names:
        if name not in entity_type.names():
            raise Refusal("property", name)
    return names


def check_options(request: Request, allowed: set[str]) -> None:
    for name in request.query_params:
        if name == "$apply":
            raise Refusal("apply")
        if name.startswith("$") and name not in allowed:
            raise Refusal("option", name)


def listing(request: Request, rows: list, fields: dict, filter_text: str | None = None):
    params = request.query_params
    query = ListQuery(filter_text if filter_text is not None else params.get("$filter"), None, params.get("$orderby"), params.get("$top"), params.get("$skip"), params.get("$count"))
    try:
        return apply_list_query(rows, query, fields)
    except InvalidQuery as error:
        token = (params.get("$filter") if error.target == "$filter" else params.get("$orderby") or "").split(" ")[0]
        raise Refusal("parse" if error.target in ("$filter", "$orderby") else "value", token or error.target) from error


def with_keys(select: list[str] | None, keys: tuple[str, ...]) -> list[str]:
    chosen = list(select or [])
    return chosen + [key for key in keys if chosen and key not in chosen]


def context(entity: str, select: list[str] | None, expand_select: list[str] | None, nav: str, keys: tuple[str, ...] = (), expand_keys: tuple[str, ...] = ()) -> str:
    parts = with_keys(select, keys)
    if nav:
        parts.append(f"{nav}({','.join(with_keys(expand_select, expand_keys))})")
    return "$metadata#" + entity + (f"({','.join(parts)})" if parts else "")


def list_body(context_text: str, rows: list, total: int | None, metadata_etag: str) -> dict:
    body = {"@odata.context": context_text, "@odata.metadataEtag": metadata_etag}
    if total is not None:
        body["@odata.count"] = total
    return body | {"value": rows}


def entity_body(context_text: str, row: dict, metadata_etag: str) -> dict:
    return {"@odata.context": context_text + "/$entity", "@odata.metadataEtag": metadata_etag} | row


def refusal_response(error: Refusal, component_id: str, service_id: str) -> tuple[int, dict]:
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
    body["innererror"] = {
        "ErrorDetails": {
            "@SAP__common.Application": {"ComponentId": component_id, "ServiceRepository": "SRVD_A2X", "ServiceId": service_id, "ServiceVersion": "0001"},
            "@SAP__common.TransactionId": uuid.uuid4().hex.upper(),
            "@SAP__common.Timestamp": stamp(),
            "@SAP__common.ErrorResolution": RESOLUTION,
        }
    }
    return status, {"error": body}
