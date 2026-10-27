from decimal import Decimal

import pytest

from butterfly.infrastructure.api.odata import ROOT
from conftest import ORDERS, make_client

URL = ROOT + "SalesOrder"
KEY = "0000012002"
ITEM_FIELDS = [
    "SalesOrder", "SalesOrderItem", "Material", "MaterialDescription",
    "Quantity", "QuantityUnit", "NetAmount",
]


def order(key=KEY):
    return next(o for o in ORDERS if o.sales_order == key)


class TestExpandSingleOrder:
    def get(self, expand="_Item"):
        return make_client().get(f"{URL}('{KEY}')", params={"$expand": expand})

    def test_context_etag_and_items_follow_the_contract(self):
        body = self.get().json()

        assert body["@odata.context"] == "$metadata#SalesOrder(_Item())/$entity"
        assert body["@odata.etag"].startswith('W/"')
        assert [item["SalesOrderItem"] for item in body["_Item"]] == [
            item.sales_order_item for item in order().items
        ]

    def test_items_come_after_the_header_fields(self):
        assert list(self.get().json())[-1] == "_Item"

    def test_item_has_every_field_in_contract_order(self):
        assert list(self.get().json()["_Item"][0]) == ITEM_FIELDS

    def test_item_amounts_are_strings(self):
        item = self.get().json()["_Item"][0]

        assert item["Quantity"].count(".") == 1 and len(item["Quantity"].split(".")[1]) == 3
        assert len(item["NetAmount"].split(".")[1]) == 2

    def test_item_numbers_keep_leading_zeros(self):
        assert self.get().json()["_Item"][0]["SalesOrderItem"] == "000010"

    def test_every_item_belongs_to_the_order(self):
        assert {item["SalesOrder"] for item in self.get().json()["_Item"]} == {KEY}

    def test_item_amounts_add_up_to_the_order_total(self):
        body = self.get().json()

        assert sum(Decimal(i["NetAmount"]) for i in body["_Item"]) == Decimal(body["TotalNetAmount"])

    def test_without_expand_there_are_no_items(self):
        assert "_Item" not in make_client().get(f"{URL}('{KEY}')").json()

    def test_unknown_order_is_still_404(self):
        response = make_client().get(f"{URL}('0000099999')", params={"$expand": "_Item"})

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "SALES_ORDER_NOT_FOUND"

    def test_other_query_options_on_one_order_are_unsupported(self):
        response = make_client().get(f"{URL}('{KEY}')", params={"$select": "SalesOrder"})

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "UNSUPPORTED_QUERY_OPTION"
        assert response.json()["error"]["target"] == "$select"


class TestExpandCollection:
    def get(self, **params):
        return make_client().get(URL, params={f"${k}": v for k, v in params.items()})

    def test_every_row_carries_its_items(self):
        body = self.get(expand="_Item").json()

        assert body["@odata.context"] == "$metadata#SalesOrder(_Item())"
        assert len(body["value"]) == len(ORDERS)
        for row, source in zip(body["value"], ORDERS):
            assert len(row["_Item"]) == len(source.items)

    def test_rows_still_carry_no_etag(self):
        assert "@odata.etag" not in self.get(expand="_Item").json()["value"][0]

    def test_select_limits_the_header_but_not_the_items(self):
        body = self.get(expand="_Item", select="SalesOrder").json()

        assert body["@odata.context"] == "$metadata#SalesOrder(SalesOrder,_Item())"
        assert list(body["value"][0]) == ["SalesOrder", "_Item"]
        assert list(body["value"][0]["_Item"][0]) == ITEM_FIELDS

    def test_works_with_filter_top_skip_and_count(self):
        body = self.get(
            expand="_Item", filter="OverallStatus eq 'A'", top="2", skip="1", count="true"
        ).json()

        matching = [o for o in ORDERS if o.overall_status == "A"]
        assert body["@odata.count"] == len(matching)
        assert [r["SalesOrder"] for r in body["value"]] == [o.sales_order for o in matching[1:3]]
        assert all("_Item" in row for row in body["value"])

    def test_no_matching_orders_gives_an_empty_list(self):
        assert self.get(expand="_Item", filter="OverallStatus eq 'Z'").json()["value"] == []

    def test_repeating_the_name_is_harmless(self):
        assert self.get(expand="_Item,_Item").status_code == 200

    def test_spaces_around_the_name_are_allowed(self):
        assert self.get(expand=" _Item ").status_code == 200


class TestInvalidExpand:
    @pytest.mark.parametrize("text", ["Other", "_item", "", "_Item,Other", "_Item($select=Material)", "*"])
    @pytest.mark.parametrize("path", ["SalesOrder", "SalesOrder('0000012002')"])
    def test_is_400_invalid_query_on_expand(self, path, text):
        response = make_client().get(ROOT + path, params={"$expand": text})

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_QUERY"
        assert response.json()["error"]["target"] == "$expand"
