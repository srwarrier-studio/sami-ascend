import copy
import json

import pytest

from butterfly.infrastructure.api.odata import ROOT
from conftest import ORDERS, make_client

URL = ROOT + "SalesOrder"

BODY = {
    "SalesOrderType": "OR",
    "SoldToParty": "0000100001",
    "RequestedDeliveryDate": "2026-11-05",
    "TransactionCurrency": "INR",
    "_Item": [
        {"Material": "RM-1001", "Quantity": "50.000", "QuantityUnit": "KG"},
        {"Material": "RM-1002", "Quantity": "25.000", "QuantityUnit": "KG"},
    ],
}


def body(**changes):
    result = copy.deepcopy(BODY)
    result.update(changes)
    return result


class TestCreateOverHttp:
    def setup_method(self):
        self.client = make_client()
        self.response = self.client.post(URL, json=BODY)

    def test_is_201_with_json(self):
        assert self.response.status_code == 201
        assert self.response.headers["content-type"].startswith("application/json")

    def test_location_points_to_the_new_order(self):
        location = self.response.headers["location"]

        assert location.endswith(ROOT + "SalesOrder('0000012031')")
        assert self.client.get(location).status_code == 200

    def test_response_is_the_full_order_with_items_and_etag(self):
        data = self.response.json()

        assert data["@odata.context"] == "$metadata#SalesOrder(_Item())/$entity"
        assert data["@odata.etag"] == 'W/"20261027091530"'
        assert data["SalesOrder"] == "0000012031"
        assert data["CustomerName"] == "Acme Industries"
        assert data["TotalNetAmount"] == "125000.00"
        assert data["OverallStatus"] == "A"
        assert data["CreatedByUser"] == "BUTTERFLY"
        assert data["CreationDateTime"] == "2026-10-27T09:15:30Z"
        assert [i["SalesOrderItem"] for i in data["_Item"]] == ["000010", "000020"]
        assert data["_Item"][0]["MaterialDescription"] == "Steel rod 12mm"

    def test_etag_matches_a_later_read(self):
        read = self.client.get(f"{URL}('0000012031')").json()

        assert read["@odata.etag"] == self.response.json()["@odata.etag"]


class TestCreatedOrderIsVisibleInReads:
    def setup_method(self):
        self.client = make_client()
        self.client.post(URL, json=BODY)

    def test_in_the_list_with_count(self):
        data = self.client.get(URL, params={"$count": "true"}).json()

        assert data["@odata.count"] == len(ORDERS) + 1
        assert data["value"][-1]["SalesOrder"] == "0000012031"

    def test_by_filter_on_the_new_status_and_user(self):
        rows = self.client.get(URL, params={"$filter": "CreatedByUser eq 'BUTTERFLY'"}).json()["value"]

        assert [row["SalesOrder"] for row in rows] == ["0000012031"]

    def test_with_expand(self):
        rows = self.client.get(URL, params={"$filter": "SalesOrder eq '0000012031'", "$expand": "_Item"}).json()["value"]

        assert len(rows[0]["_Item"]) == 2

    def test_through_the_item_path(self):
        items = self.client.get(f"{URL}('0000012031')/_Item").json()["value"]

        assert [i["Material"] for i in items] == ["RM-1001", "RM-1002"]

    def test_second_create_gets_the_next_number(self):
        second = self.client.post(URL, json=BODY)

        assert second.json()["SalesOrder"] == "0000012032"
        assert self.client.get(URL, params={"$count": "true", "$top": "0"}).json()["@odata.count"] == len(ORDERS) + 2

    def test_existing_orders_are_not_changed(self):
        first = self.client.get(f"{URL}('0000012001')").json()

        assert first["SalesOrder"] == "0000012001"
        assert first["OverallStatus"] == ORDERS[0].overall_status


class TestCreateValidationOverHttp:
    def test_is_400_with_every_problem_in_details(self):
        client = make_client()
        response = client.post(
            URL,
            json=body(
                SoldToParty="0000999999",
                _Item=[{"Material": "RM-1001", "Quantity": "0", "QuantityUnit": "KG"}],
            ),
        )

        assert response.status_code == 400
        assert response.json() == {
            "error": {
                "code": "VALIDATION_FAILED",
                "message": "The sales order has errors.",
                "details": [
                    {
                        "code": "CUSTOMER_UNKNOWN",
                        "message": "Customer 0000999999 does not exist.",
                        "target": "SoldToParty",
                    },
                    {
                        "code": "QUANTITY_NOT_POSITIVE",
                        "message": "Quantity must be greater than 0.",
                        "target": "_Item/0/Quantity",
                    },
                ],
            }
        }

    def test_nothing_is_created(self):
        client = make_client()
        client.post(URL, json=body(TransactionCurrency="USD"))

        assert client.get(URL, params={"$count": "true", "$top": "0"}).json()["@odata.count"] == len(ORDERS)

    def test_a_failed_create_does_not_use_up_a_number(self):
        client = make_client()
        client.post(URL, json=body(TransactionCurrency="USD"))

        assert client.post(URL, json=BODY).json()["SalesOrder"] == "0000012031"

    def test_sap_filled_fields_are_rejected(self):
        response = make_client().post(URL, json=body(OverallStatus="C", SalesOrder="0000000001"))

        targets = [d["target"] for d in response.json()["error"]["details"]]
        assert response.status_code == 400
        assert targets == ["OverallStatus", "SalesOrder"]


class TestInvalidRequestBody:
    @pytest.mark.parametrize(
        "content",
        [b"", b"not json", b"{", b"[]", b'[{"a": 1}]', b'"text"', b"5", b"null", b"true", b"\xff\xfe"],
        ids=["empty", "text", "unclosed", "array", "array of objects", "string", "number", "null", "boolean", "bad bytes"],
    )
    def test_is_400_invalid_request_body(self, content):
        response = make_client().post(URL, content=content, headers={"Content-Type": "application/json"})

        assert response.status_code == 400
        assert response.json() == {
            "error": {
                "code": "INVALID_REQUEST_BODY",
                "message": "The request body must be a JSON object.",
                "target": "body",
            }
        }

    def test_empty_object_is_a_validation_error_not_a_body_error(self):
        response = make_client().post(URL, json={})

        assert response.json()["error"]["code"] == "VALIDATION_FAILED"

    def test_body_is_read_even_without_a_content_type_header(self):
        response = make_client().post(URL, content=json.dumps(BODY))

        assert response.status_code == 201


class TestOtherMethodsAndPaths:
    def test_delete_is_405_in_the_error_format(self):
        response = make_client().delete(f"{URL}('0000012001')")

        assert response.status_code == 405
        assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"

    def test_put_is_405(self):
        assert make_client().put(f"{URL}('0000012001')", json={}).status_code == 405

    def test_unknown_path_is_404_in_the_error_format(self):
        response = make_client().get(ROOT + "Customer")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"
        assert response.json()["error"]["message"]
