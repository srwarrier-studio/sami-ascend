import pytest

from butterfly.infrastructure.api.odata import ROOT
from conftest import ORDERS, make_client

KEY = "0000012002"
URL = f"{ROOT}SalesOrder('{KEY}')/_Item"
ITEMS = next(o for o in ORDERS if o.sales_order == KEY).items
NUMBERS = [item.sales_order_item for item in ITEMS]


def get(**params):
    return make_client().get(URL, params={f"${k}": v for k, v in params.items()})


def numbers(response):
    return [row["SalesOrderItem"] for row in response.json()["value"]]


class TestListOrderItems:
    def test_returns_the_items_of_that_order_only(self):
        body = get().json()

        assert body["@odata.context"] == "$metadata#SalesOrder('0000012002')/_Item"
        assert numbers(get()) == NUMBERS
        assert {row["SalesOrder"] for row in body["value"]} == {KEY}

    def test_default_order_is_by_item_number(self):
        assert numbers(get()) == sorted(NUMBERS)

    def test_contract_example_orderby_item_number(self):
        assert numbers(get(orderby="SalesOrderItem")) == sorted(NUMBERS)

    def test_orderby_descending(self):
        assert numbers(get(orderby="SalesOrderItem desc")) == sorted(NUMBERS, reverse=True)

    def test_orderby_decimal_amount(self):
        expected = [i.sales_order_item for i in sorted(ITEMS, key=lambda i: i.net_amount, reverse=True)]
        assert numbers(get(orderby="NetAmount desc")) == expected

    def test_unknown_order_is_404_in_the_error_format(self):
        response = make_client().get(f"{ROOT}SalesOrder('0000099999')/_Item")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "SALES_ORDER_NOT_FOUND"
        assert response.json()["error"]["target"] == "SalesOrder"

    def test_items_are_not_shared_between_orders(self):
        other = make_client().get(f"{ROOT}SalesOrder('0000012001')/_Item").json()["value"]

        assert {row["SalesOrder"] for row in other} == {"0000012001"}


class TestItemFilter:
    def test_on_text_field(self):
        material = ITEMS[0].material
        expected = [i.sales_order_item for i in ITEMS if i.material == material]
        assert numbers(get(filter=f"Material eq '{material}'")) == expected

    def test_on_decimal_field(self):
        expected = [i.sales_order_item for i in ITEMS if i.quantity > 10]
        assert numbers(get(filter="Quantity gt 10")) == expected

    def test_with_contains(self):
        description = ITEMS[0].material_description.split()[0]
        assert numbers(get(filter=f"contains(MaterialDescription,'{description}')"))

    def test_with_and(self):
        assert numbers(get(filter="Quantity gt 0 and NetAmount gt 0")) == NUMBERS

    def test_matching_nothing_gives_an_empty_list(self):
        assert get(filter="Material eq 'NOPE'").json()["value"] == []

    def test_an_order_field_is_not_an_item_field(self):
        response = get(filter="CustomerName eq 'Acme Industries'")

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_QUERY"
        assert response.json()["error"]["target"] == "$filter"


class TestItemSelectAndPaging:
    def test_select(self):
        body = get(select="Material,Quantity").json()

        assert body["@odata.context"] == "$metadata#SalesOrder('0000012002')/_Item(Material,Quantity)"
        assert list(body["value"][0]) == ["Material", "Quantity"]

    def test_top_and_skip(self):
        assert numbers(get(top="1", skip="1")) == NUMBERS[1:2]

    def test_count(self):
        body = get(count="true", top="1").json()

        assert body["@odata.count"] == len(ITEMS)
        assert len(body["value"]) == 1

    def test_skip_beyond_the_items_gives_an_empty_list(self):
        assert get(skip="50").json()["value"] == []


class TestInvalidItemQuery:
    def test_select_of_an_order_field_is_400(self):
        response = get(select="CustomerName")

        assert response.status_code == 400
        assert response.json()["error"]["target"] == "$select"

    def test_orderby_of_an_order_field_is_400(self):
        assert get(orderby="OrderDate").status_code == 400

    def test_expand_on_items_is_unsupported(self):
        response = get(expand="_Item")

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "UNSUPPORTED_QUERY_OPTION"
        assert response.json()["error"]["target"] == "$expand"

    @pytest.mark.parametrize("name", ["$apply", "$search"])
    def test_other_unsupported_options_are_400(self, name):
        assert make_client().get(URL, params={name: "x"}).status_code == 400
