import json
import re

import pytest

from butterfly.infrastructure.api.odata import ROOT
from conftest import ORDERS, make_client
from contract_helpers import CONTRACT, error_example, order_example, same_shape

URL = ROOT + "SalesOrder"
POST_BODY = re.compile(r"```\nPOST \{root\}SalesOrder\n```\n\n```json\n(.*?)\n```", re.DOTALL)
PATCH_BODY = re.compile(
    r"```\nPATCH \{root\}SalesOrder\('0000012345'\)\nIf-Match: [^\n]+\n```\n\n```json\n(.*?)\n```",
    re.DOTALL,
)
KEY = next(o.sales_order for o in ORDERS if o.overall_status == "A")


def create_example() -> dict:
    return json.loads(POST_BODY.search(CONTRACT).group(1))


def change_example() -> dict:
    return json.loads(PATCH_BODY.search(CONTRACT).group(1))


class TestContractCreateExample:
    def test_the_example_request_was_found(self):
        assert create_example()["_Item"]

    def test_example_request_is_accepted_with_201(self):
        response = make_client().post(URL, json=create_example())

        assert response.status_code == 201

    def test_response_has_the_shape_of_the_order_with_items_example(self):
        response = make_client().post(URL, json=create_example())

        same_shape(response.json(), order_example("$metadata#SalesOrder(_Item())/$entity"))

    def test_response_totals_and_item_numbers_follow_the_contract_text(self):
        data = make_client().post(URL, json=create_example()).json()

        assert [i["SalesOrderItem"] for i in data["_Item"]] == ["000010", "000020"]
        assert data["OverallStatus"] == "A"
        assert data["OrderDate"] == "2026-10-27"


class TestContractCreateErrorExamples:
    def test_customer_and_quantity_example_matches_exactly(self):
        request = create_example()
        request["SoldToParty"] = "0000999999"
        request["_Item"][1]["Quantity"] = "0"

        response = make_client().post(URL, json=request)

        assert response.status_code == 400
        assert response.json() == error_example("VALIDATION_FAILED", "CUSTOMER_UNKNOWN")

    def test_format_and_not_allowed_example_matches_exactly(self):
        request = create_example()
        request["RequestedDeliveryDate"] = "tomorrow"
        request["OverallStatus"] = "C"

        response = make_client().post(URL, json=request)

        assert response.status_code == 400
        assert response.json() == error_example("VALIDATION_FAILED", "FIELD_NOT_ALLOWED")

    def test_invalid_body_example_matches_exactly(self):
        response = make_client().post(URL, content=b"not json")

        assert response.status_code == 400
        assert response.json() == error_example("INVALID_REQUEST_BODY")

    def test_every_detail_code_the_contract_lists_can_be_produced(self):
        listed = set(re.findall(r"`([A-Z_]{5,})`", CONTRACT.split("Detail codes:")[1].split("\n\n")[0]))
        client = make_client()
        seen = set()
        for change in [
            {"SalesOrderType": None},
            {"RequestedDeliveryDate": "x", "Colour": 1},
            {"SoldToParty": "0000999999", "TransactionCurrency": "USD", "RequestedDeliveryDate": "2020-01-01"},
            {"_Item": []},
            {"_Item": [{"Material": "RM-9999", "Quantity": "0", "QuantityUnit": "EA"}]},
            {"_Item": [{"Material": "RM-1001", "Quantity": "1", "QuantityUnit": "EA"}]},
        ]:
            response = client.post(URL, json=create_example() | change)
            seen |= {d["code"] for d in response.json()["error"]["details"]}
        seen |= {d["code"] for d in self.change_completed_order(client)}

        assert listed <= seen, f"never produced: {sorted(listed - seen)}"

    def change_completed_order(self, client):
        key = next(o.sales_order for o in ORDERS if o.overall_status == "C")
        etag = client.get(f"{URL}('{key}')").json()["@odata.etag"]
        response = client.patch(
            f"{URL}('{key}')", json=change_example(), headers={"If-Match": etag}
        )
        return response.json()["error"]["details"]


class TestContractChangeExamples:
    def patch(self, client, etag=None, body=None):
        etag = etag or client.get(f"{URL}('{KEY}')").json()["@odata.etag"]
        return client.patch(f"{URL}('{KEY}')", json=body or change_example(), headers={"If-Match": etag})

    def test_example_request_returns_200(self):
        assert self.patch(make_client()).status_code == 200

    def test_response_has_the_shape_of_the_single_order_example(self):
        response = self.patch(make_client())

        same_shape(response.json(), order_example("$metadata#SalesOrder/$entity"))
        assert response.json()["RequestedDeliveryDate"] == change_example()["RequestedDeliveryDate"]

    def test_stale_etag_matches_the_412_example_exactly(self):
        response = self.patch(make_client(), etag='W/"20200101000000"')

        assert response.status_code == 412
        assert response.json() == error_example("ETAG_MISMATCH")

    def test_missing_if_match_is_428_with_the_same_shape(self):
        response = make_client().patch(f"{URL}('{KEY}')", json=change_example())

        assert response.status_code == 428
        assert set(response.json()["error"]) == set(error_example("ETAG_MISMATCH")["error"])
        assert response.json()["error"]["code"] == "ETAG_REQUIRED"


class TestContractGenericErrorExamples:
    def test_unknown_path_matches_the_404_example_exactly(self):
        response = make_client().get(ROOT + "Customer")

        assert response.status_code == 404
        assert response.json() == error_example("RESOURCE_NOT_FOUND")

    @pytest.mark.parametrize("method", ["delete", "put"])
    def test_unsupported_method_matches_the_405_example_exactly(self, method):
        response = getattr(make_client(), method)(f"{URL}('{KEY}')")

        assert response.status_code == 405
        assert response.json() == error_example("METHOD_NOT_ALLOWED")
