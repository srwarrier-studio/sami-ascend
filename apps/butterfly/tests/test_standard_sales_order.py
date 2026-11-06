import json
import re
from decimal import Decimal
from pathlib import Path

import pytest
from conftest import ORDERS, make_client

from butterfly.application.alpha import external as ext
from butterfly.domain.entities.master_data import SALES_ORGANIZATIONS
from butterfly.domain.entities.sales_order import SalesOrder
from butterfly.infrastructure.api.standard.dialects import V2_ROOT, V4_ROOT
from butterfly.infrastructure.api.standard.edmx import SPECS, V2_METADATA, V4_METADATA

V4 = V4_ROOT
V2 = V2_ROOT
REAL_V4 = json.loads((SPECS / "api_salesorder-v4" / "list-top3.json").read_text())["value"][0]
REAL_V2 = json.loads((SPECS / "api_sales_order_srv-v2" / "list-top3.json").read_text())["d"]["results"][0]
FIRST = ORDERS[0]
KEY = FIRST.sales_order
TOTAL = len(ORDERS)


def kind(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def same_kinds(actual: dict, real: dict) -> list[str]:
    return [name for name in real if real[name] is not None and actual[name] is not None and kind(actual[name]) != kind(real[name])]


@pytest.fixture(scope="module")
def client():
    return make_client()


def get(client, path):
    response = client.get(path)
    return response, response.json() if "json" in response.headers["content-type"] else response.text


class TestTheRealMetadata:
    def test_the_v4_metadata_is_the_saved_real_document(self, client):
        assert client.get(f"{V4}/$metadata").content == V4_METADATA.read_bytes()

    def test_the_v2_metadata_is_the_saved_real_document(self, client):
        assert client.get(f"{V2}/$metadata").content == V2_METADATA.read_bytes()


class TestAV4Row:
    def test_has_exactly_the_properties_of_the_real_row(self, client):
        row = get(client, f"{V4}/SalesOrder?$top=1")[1]["value"][0]
        assert list(row) == list(REAL_V4)
        assert same_kinds(row, REAL_V4) == []

    def test_carries_the_order_values_the_real_names(self, client):
        row = get(client, f"{V4}/SalesOrder?$filter=SalesOrder eq '{KEY}'")[1]["value"][0]
        assert row["SalesOrder"] == KEY.lstrip("0")
        assert row["SoldToParty"] == ext(FIRST.sold_to_party) and row["SalesOrderType"] == FIRST.sales_order_type
        assert row["BillingCompanyCode"] == FIRST.company_code
        assert row["SalesOrganization"] == SALES_ORGANIZATIONS[FIRST.company_code]
        assert row["SalesOrderDate"] == FIRST.order_date.isoformat()
        assert row["TotalNetAmount"] == float(FIRST.total_net_amount) and isinstance(row["TotalNetAmount"], float)
        assert row["TransactionCurrency"] == FIRST.transaction_currency
        assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}(\.\d+)?Z", row["LastChangeDateTime"])
        assert re.fullmatch(r"\d{2}:\d{2}:\d{2}", row["CreationTime"])

    def test_the_context_and_etags_are_the_real_kind(self, client):
        body = get(client, f"{V4}/SalesOrder?$top=1")[1]
        assert body["@odata.context"] == "$metadata#SalesOrder" and body["@odata.metadataEtag"].startswith('W/"')
        assert body["value"][0]["@odata.etag"].startswith('W/"')


class TestAV2Row:
    def test_has_exactly_the_properties_of_the_real_row(self, client):
        row = get(client, f"{V2}/A_SalesOrder?$top=1")[1]["d"]["results"][0]
        assert list(row) == list(REAL_V2)
        assert same_kinds({k: v for k, v in row.items() if k != "__metadata"}, {k: v for k, v in REAL_V2.items() if k != "__metadata"}) == []

    def test_the_etag_is_the_v2_datetimeoffset_kind(self, client):
        etag = get(client, f"{V2}/A_SalesOrder?$top=1")[1]["d"]["results"][0]["__metadata"]["etag"]
        real = REAL_V2["__metadata"]["etag"]
        shape = re.compile(r"W/\"datetimeoffset'\d{4}-\d{2}-\d{2}T\d{2}%3A\d{2}%3A\d{2}\.\d{7}Z'\"")
        assert shape.fullmatch(etag) and shape.fullmatch(real)

    def test_has_no_company_field_like_sap(self, client):
        row = get(client, f"{V2}/A_SalesOrder?$top=1")[1]["d"]["results"][0]
        assert not [name for name in row if "Company" in name]
        assert row["SalesOrganization"] == SALES_ORGANIZATIONS[FIRST.company_code]

    def test_uses_the_v2_formats(self, client):
        row = get(client, f"{V2}/A_SalesOrder?$filter=SalesOrder eq '{KEY}'")[1]["d"]["results"][0]
        assert re.fullmatch(r"/Date\(\d+\)/", row["SalesOrderDate"])
        assert re.fullmatch(r"/Date\(\d+\+0000\)/", row["LastChangeDateTime"])
        assert row["TotalNetAmount"] == format(FIRST.total_net_amount, "f")
        assert row["__metadata"]["type"] == "API_SALES_ORDER_SRV.A_SalesOrderType"
        assert row["__metadata"]["uri"].endswith(f"A_SalesOrder('{KEY.lstrip('0')}')")
        assert row["to_Item"]["__deferred"]["uri"].endswith("/to_Item")


class TestV4QueryOptions:
    def test_top_skip_and_count(self, client):
        body = get(client, f"{V4}/SalesOrder?$top=2&$skip=1&$count=true")[1]
        assert len(body["value"]) == 2 and body["@odata.count"] == TOTAL
        assert "@odata.count" not in get(client, f"{V4}/SalesOrder?$top=1")[1]

    def test_the_count_segment_is_plain_text(self, client):
        response, text = get(client, f"{V4}/SalesOrder/$count")
        assert response.headers["content-type"].startswith("text/plain") and text == str(TOTAL)

    def test_select_keeps_the_etag_and_the_key(self, client):
        row = get(client, f"{V4}/SalesOrder?$top=1&$select=SalesOrderDate,TotalNetAmount")[1]["value"][0]
        assert list(row) == ["@odata.etag", "SalesOrder", "SalesOrderDate", "TotalNetAmount"]

    def test_filter_and_orderby(self, client):
        currency = FIRST.transaction_currency
        path = f"{V4}/SalesOrder?$filter=TotalNetAmount gt 0 and TransactionCurrency eq '{currency}'&$orderby=TotalNetAmount desc&$select=TotalNetAmount&$count=true"
        body = get(client, path)[1]
        amounts = [row["TotalNetAmount"] for row in body["value"]]
        assert amounts == sorted(amounts, reverse=True)
        assert body["@odata.count"] == len([o for o in ORDERS if o.transaction_currency == currency and o.total_net_amount > 0])

    def test_expand_with_a_nested_select(self, client):
        body = get(client, f"{V4}/SalesOrder?$top=1&$select=SalesOrderDate&$expand=_Item($select=SalesOrderItem,Product,NetAmount)")[1]
        assert body["@odata.context"] == "$metadata#SalesOrder(SalesOrderDate,_Item(SalesOrderItem,Product,NetAmount))"
        item = body["value"][0]["_Item"][0]
        assert list(item) == ["@odata.etag", "SalesOrder", "SalesOrderItem", "Product", "NetAmount"]
        assert item["SalesOrderItem"] == FIRST.items[0].sales_order_item.lstrip("0") and item["Product"] == FIRST.items[0].material

    def test_one_order_by_key_with_or_without_leading_zeros(self, client):
        body = get(client, f"{V4}/SalesOrder('{KEY}')")[1]
        assert body["@odata.context"] == "$metadata#SalesOrder/$entity" and body["SalesOrder"] == KEY.lstrip("0")
        assert get(client, f"{V4}/SalesOrder('{KEY.lstrip('0')}')")[1]["SalesOrder"] == KEY.lstrip("0")

    def test_the_items_of_one_order_and_the_item_set(self, client):
        items = get(client, f"{V4}/SalesOrder('{KEY}')/_Item")[1]["value"]
        assert [i["Product"] for i in items] == [i.material for i in FIRST.items]
        assert items[0]["RequestedQuantityISOUnit"] in ("KGM", FIRST.items[0].quantity_unit)
        every = get(client, f"{V4}/SalesOrderItem?$top=1000&$count=true")[1]
        assert every["@odata.count"] == sum(len(o.items) for o in ORDERS)

    def test_the_other_entity_sets_exist_and_are_empty(self, client):
        for name in ("SalesOrderPartner", "SalesOrderScheduleLine", "SalesOrderText"):
            assert get(client, f"{V4}/{name}")[1]["value"] == []


class TestV4Refusals:
    def test_an_unknown_filter_property_is_the_real_parser_error(self, client):
        response, body = get(client, f"{V4}/SalesOrder?$filter=Nope eq 1")
        assert response.status_code == 400 and body["error"]["message"] == "Invalid token 'Nop...' at position '1'"
        assert body["error"]["code"].startswith("/IWCOR/CX_OD_EXPR_PARSER_ERROR/")
        assert body["error"]["innererror"]["ErrorDetails"]["@SAP__common.Application"]["ServiceId"] == "API_SALESORDER"

    def test_an_amount_filter_without_the_currency_is_refused(self, client):
        response, body = get(client, f"{V4}/SalesOrder?$filter=TotalNetAmount gt 100")
        assert response.status_code == 400 and body["error"]["code"] == "/IWBEP/CM_V4S_RUN/031"
        assert body["error"]["message"] == "Filter contains unit/currency amount 'TotalNetAmount' without matching unit/currency"

    def test_an_unknown_select_property_is_refused(self, client):
        response, body = get(client, f"{V4}/SalesOrder?$select=Nope")
        assert response.status_code == 400 and body["error"]["message"] == "Property 'Nop...' not found"


class TestV4Apply:
    def test_groups_and_sums_like_the_service(self, client):
        body = get(client, f"{V4}/SalesOrder?$apply=groupby((SoldToParty,TransactionCurrency),aggregate(TotalNetAmount with sum as Total))&$top=1000")[1]
        expected: dict = {}
        for order in ORDERS:
            expected[(ext(order.sold_to_party), order.transaction_currency)] = expected.get((ext(order.sold_to_party), order.transaction_currency), Decimal(0)) + order.total_net_amount
        assert body["@odata.context"] == "$metadata#SalesOrder(SoldToParty,TransactionCurrency,Total)"
        assert {(r["SoldToParty"], r["TransactionCurrency"]): Decimal(str(r["Total"])) for r in body["value"]} == expected
        assert all(r["Total@odata.type"] == "#Decimal" and r["@odata.etag"] == 'W/""' for r in body["value"])

    def test_a_filter_step_comes_first(self, client):
        day = FIRST.order_date.isoformat()
        body = get(client, f"{V4}/SalesOrder?$apply=filter(SalesOrderDate eq {day})/groupby((BillingCompanyCode,TransactionCurrency),aggregate(TotalNetAmount with sum as Total))")[1]
        wanted = sum(o.total_net_amount for o in ORDERS if o.order_date == FIRST.order_date and o.company_code == FIRST.company_code and o.transaction_currency == FIRST.transaction_currency)
        mine = next(r for r in body["value"] if r["BillingCompanyCode"] == FIRST.company_code and r["TransactionCurrency"] == FIRST.transaction_currency)
        assert Decimal(str(mine["Total"])) == wanted

    def test_items_group_by_product(self, client):
        body = get(client, f"{V4}/SalesOrderItem?$apply=groupby((Product,TransactionCurrency),aggregate(NetAmount with sum as Total))&$top=1000")[1]
        assert {r["Product"] for r in body["value"]} == {i.material for o in ORDERS for i in o.items}

    def test_ordering_by_the_total_is_refused_like_sap(self, client):
        response, body = get(client, f"{V4}/SalesOrder?$apply=groupby((SoldToParty),aggregate(TotalNetAmount with sum as Total))&$orderby=Total desc")
        assert response.status_code == 400 and body["error"]["message"] == "Invalid token 'Tot...' at position '1'"

    def test_countdistinct_is_not_supported_like_sap(self, client):
        response, body = get(client, f"{V4}/SalesOrder?$apply=groupby((SoldToParty),aggregate(SalesOrder with countdistinct as N))")
        assert response.status_code == 501
        assert body["error"]["code"] == "SADL_GW/007" and body["error"]["message"] == "$apply option not supported"


class TestV2QueryOptions:
    def test_inlinecount_is_a_string_in_d(self, client):
        body = get(client, f"{V2}/A_SalesOrder?$top=1&$inlinecount=allpages")[1]
        assert body["d"]["__count"] == str(TOTAL) and len(body["d"]["results"]) == 1
        assert "__count" not in get(client, f"{V2}/A_SalesOrder?$top=1")[1]["d"]

    def test_the_count_segment_is_plain_text(self, client):
        assert get(client, f"{V2}/A_SalesOrder/$count")[1] == str(TOTAL)

    def test_select_and_expand_together(self, client):
        row = get(client, f"{V2}/A_SalesOrder?$top=1&$select=SalesOrder,TotalNetAmount&$expand=to_Item")[1]["d"]["results"][0]
        assert list(row) == ["__metadata", "SalesOrder", "TotalNetAmount", "to_Item"]
        items = row["to_Item"]["results"]
        assert [i["Material"] for i in items] == [i.material for i in FIRST.items] and items[0]["RequestedQuantityUnit"]

    def test_a_v2_date_literal_and_a_decimal_filter(self, client):
        day = FIRST.order_date.isoformat()
        path = f"{V2}/A_SalesOrder?$filter=SalesOrderDate eq datetime'{day}T00:00:00' and TotalNetAmount gt 0M&$inlinecount=allpages"
        body = get(client, path)[1]["d"]
        assert int(body["__count"]) == len([o for o in ORDERS if o.order_date == FIRST.order_date and o.total_net_amount > 0])

    def test_a_single_order_and_its_items(self, client):
        row = get(client, f"{V2}/A_SalesOrder('{KEY}')")[1]["d"]
        assert row["SalesOrder"] == KEY.lstrip("0")
        assert len(get(client, f"{V2}/A_SalesOrder('{KEY}')/to_Item")[1]["d"]["results"]) == len(FIRST.items)

    def test_the_other_entity_sets_exist_and_are_empty(self, client):
        assert get(client, f"{V2}/A_SalesOrderHeaderPartner")[1]["d"]["results"] == []


class TestV2Refusals:
    def test_an_unknown_property_is_the_real_message(self, client):
        response, body = get(client, f"{V2}/A_SalesOrder?$filter=Nope eq 1")
        assert response.status_code == 400
        assert body["error"]["message"] == {"lang": "en", "value": "Property Nope not found in type A_SalesOrderType"}

    def test_apply_is_not_a_v2_option(self, client):
        response, body = get(client, f"{V2}/A_SalesOrder?$apply=groupby((SoldToParty),aggregate(TotalNetAmount with sum as Total))")
        assert response.status_code == 400 and body["error"]["message"]["value"] == "Invalid system query option specified"


class TestTheStoredModel:
    def test_the_sales_organization_follows_the_company(self):
        order = SalesOrder("1", "OR", "C1", None, FIRST.order_date, None, "INR", Decimal(1), "A", "U", FIRST.creation_date_time, FIRST.last_change_date_time, company_code="INA2")
        assert (order.sales_organization, order.distribution_channel, order.division) == (SALES_ORGANIZATIONS["INA2"], "10", "00")

    def test_a_given_sales_organization_is_kept(self):
        order = SalesOrder("1", "OR", "C1", None, FIRST.order_date, None, "INR", Decimal(1), "A", "U", FIRST.creation_date_time, FIRST.last_change_date_time, sales_organization="9999", purchase_order_by_customer="PO-1")
        assert (order.sales_organization, order.purchase_order_by_customer) == ("9999", "PO-1")

    def test_the_sqlite_store_keeps_the_new_fields(self):
        from butterfly.infrastructure.sqlite.sales_order_repo import SqliteSalesOrderRepo

        order = SalesOrder("7", "OR", "C1", None, FIRST.order_date, None, "INR", Decimal(1), "A", "U", FIRST.creation_date_time, FIRST.last_change_date_time, sales_organization="9999", distribution_channel="20", division="05", purchase_order_by_customer="PO-9")
        stored = SqliteSalesOrderRepo.from_orders([order]).get("7")
        assert (stored.sales_organization, stored.distribution_channel, stored.division, stored.purchase_order_by_customer) == ("9999", "20", "05", "PO-9")


class TestCustomerNumbers:
    def test_the_sold_to_party_is_shown_without_leading_zeros_in_v4_and_v2(self, client):
        v4 = get(client, f"{V4}/SalesOrder?$top=1")[1]["value"][0]["SoldToParty"]
        v2 = get(client, f"{V2}/A_SalesOrder?$top=1")[1]["d"]["results"][0]["SoldToParty"]
        assert v4 == v2 and not v4.startswith("0")

    def test_a_filter_on_the_sold_to_party_works_with_or_without_the_zeros(self, client):
        for text in (FIRST.sold_to_party, ext(FIRST.sold_to_party)):
            body = get(client, f"{V4}/SalesOrder?$filter=SoldToParty eq '{text}'&$top=1000&$select=SoldToParty")[1]
            assert body["value"] and {r["SoldToParty"] for r in body["value"]} == {ext(FIRST.sold_to_party)}

    def test_a_filter_on_the_order_number_works_with_or_without_the_zeros(self, client):
        for text in (KEY, KEY.lstrip("0")):
            body = get(client, f"{V4}/SalesOrder?$filter=SalesOrder eq '{text}'&$select=SalesOrder")[1]
            assert [r["SalesOrder"] for r in body["value"]] == [KEY.lstrip("0")]
