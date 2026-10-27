import json
import re
from datetime import date
from pathlib import Path

import pytest

from butterfly.infrastructure.api.odata import ROOT
from conftest import ORDERS, make_client

CONTRACT = (Path(__file__).resolve().parents[3] / "docs/sap/sales-contract.md").read_text()

FIELD_ROW = re.compile(r"^\| `(\w+)` \| `(Edm\.\w+)`(?: \(([\d,]+)\))? \| (Yes|No) \|", re.MULTILINE)
EXAMPLE = re.compile(r"```\nGET \{root\}([^\n]+)\n```\n\n```json\n(.*?)\n```", re.DOTALL)
JSON_BLOCK = re.compile(r"```json\n(.*?)\n```", re.DOTALL)
SEEDED_KEY = "0000012002"


def field_table(heading: str) -> list[tuple[str, str, tuple[int, ...], bool]]:
    start = CONTRACT.index(f"### {heading} (key")
    end = CONTRACT.index("\n##", start + 1)
    return [
        (name, edm, tuple(int(n) for n in size.split(",")) if size else (), nullable == "Yes")
        for name, edm, size, nullable in FIELD_ROW.findall(CONTRACT[start:end])
    ]


ORDER_TABLE = field_table("SalesOrder")
ITEM_TABLE = field_table("SalesOrderItem")


def check_value(name, edm, size, value):
    if edm == "Edm.String":
        assert isinstance(value, str) and len(value) <= size[0], name
    elif edm == "Edm.Date":
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}", value), name
        date.fromisoformat(value)
    elif edm == "Edm.DateTimeOffset":
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value), name
    elif edm == "Edm.Decimal":
        precision, scale = size
        assert re.fullmatch(rf"-?\d+\.\d{{{scale}}}", value), f"{name}={value}"
        assert len(value.replace("-", "").replace(".", "")) <= precision, name
    else:
        pytest.fail(f"{name} has type {edm} that the check does not know")


def check_rows(rows, table):
    for row in rows:
        assert list(row) == [name for name, *_ in table]
        for name, edm, size, nullable in table:
            if row[name] is None:
                assert nullable, f"{name} is null but the contract says not nullable"
            else:
                check_value(name, edm, size, row[name])


def same_shape(actual, expected, path="body"):
    if expected is None or actual is None:
        return
    if isinstance(expected, dict):
        assert isinstance(actual, dict), path
        assert list(actual) == list(expected), f"{path}: {list(actual)} != {list(expected)}"
        for key in expected:
            same_shape(actual[key], expected[key], f"{path}.{key}")
    elif isinstance(expected, list):
        assert isinstance(actual, list), path
        if actual and expected:
            same_shape(actual[0], expected[0], f"{path}[0]")
    else:
        assert type(actual) is type(expected), f"{path}: {actual!r} vs {expected!r}"


class TestContractFieldTables:
    def test_the_tables_were_found(self):
        assert [name for name, *_ in ORDER_TABLE][:3] == ["SalesOrder", "SalesOrderType", "SoldToParty"]
        assert len(ORDER_TABLE) == 12
        assert len(ITEM_TABLE) == 7


class TestOrderMatchesFieldTable:
    def test_every_listed_order(self):
        rows = make_client().get(ROOT + "SalesOrder").json()["value"]

        assert len(rows) == len(ORDERS)
        check_rows(rows, ORDER_TABLE)

    def test_single_order_has_the_table_fields_after_the_annotations(self):
        body = make_client().get(f"{ROOT}SalesOrder('{SEEDED_KEY}')").json()

        check_rows([{k: v for k, v in body.items() if not k.startswith("@")}], ORDER_TABLE)

    def test_both_empty_and_filled_nullable_dates_are_seen(self):
        rows = make_client().get(ROOT + "SalesOrder").json()["value"]

        assert any(row["RequestedDeliveryDate"] is None for row in rows)
        assert any(row["RequestedDeliveryDate"] is not None for row in rows)


class TestItemMatchesFieldTable:
    def test_every_item_of_every_order(self):
        rows = make_client().get(ROOT + "SalesOrder", params={"$expand": "_Item"}).json()["value"]

        items = [item for row in rows for item in row["_Item"]]
        assert len(items) == sum(len(order.items) for order in ORDERS)
        check_rows(items, ITEM_TABLE)

    def test_items_through_the_navigation_path(self):
        rows = make_client().get(f"{ROOT}SalesOrder('{SEEDED_KEY}')/_Item").json()["value"]

        check_rows(rows, ITEM_TABLE)


EXAMPLES = EXAMPLE.findall(CONTRACT)


class TestContractReadExamples:
    def test_the_examples_were_found(self):
        assert len(EXAMPLES) >= 3

    @pytest.mark.parametrize("request_text,response_text", EXAMPLES, ids=[e[0][:60] for e in EXAMPLES])
    def test_response_has_the_same_shape_as_the_example(self, request_text, response_text):
        if "SalesSummary" in request_text:
            pytest.skip("summary entities are butterfly phase 03")
        response = make_client().get(ROOT + request_text.replace("0000012345", SEEDED_KEY))

        assert response.status_code == 200
        same_shape(response.json(), json.loads(response_text))


def error_example(code):
    for text in JSON_BLOCK.findall(CONTRACT):
        block = json.loads(text)
        if block.get("error", {}).get("code") == code:
            return block
    pytest.fail(f"no example with code {code}")


class TestContractErrorExamples:
    def test_not_found_matches_the_example_exactly(self):
        response = make_client().get(f"{ROOT}SalesOrder('0000099999')")

        assert response.status_code == 404
        assert response.json() == error_example("SALES_ORDER_NOT_FOUND")

    def test_unsupported_option_matches_the_example_exactly(self):
        response = make_client().get(ROOT + "SalesOrder", params={"$apply": "x"})

        assert response.status_code == 400
        assert response.json() == error_example("UNSUPPORTED_QUERY_OPTION")

    def test_invalid_query_matches_the_example_exactly(self):
        response = make_client().get(ROOT + "SalesOrder", params={"$filter": "Colour eq 'x'"})

        assert response.status_code == 400
        assert response.json() == error_example("INVALID_QUERY")

    def test_every_error_has_code_and_message_and_only_known_keys(self):
        for params in [{"$apply": "x"}, {"$top": "9999"}, {"$filter": "((("}]:
            error = make_client().get(ROOT + "SalesOrder", params=params).json()["error"]

            assert set(error) <= {"code", "message", "target", "details"}
            assert error["code"] and error["message"]
