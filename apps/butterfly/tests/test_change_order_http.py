import json

import pytest

from butterfly.infrastructure.api.odata import ROOT
from conftest import ORDERS, make_client

URL = ROOT + "SalesOrder"
KEY = next(o.sales_order for o in ORDERS if o.overall_status == "A")
DONE = next(o.sales_order for o in ORDERS if o.overall_status == "C")


def order_url(key=KEY):
    return f"{URL}('{key}')"


def etag_of(client, key=KEY):
    return client.get(order_url(key)).json()["@odata.etag"]


def patch(client, body, key=KEY, etag="read"):
    headers = {} if etag is None else {"If-Match": etag_of(client, key) if etag == "read" else etag}
    return client.patch(order_url(key), json=body, headers=headers)


class TestChangeOverHttp:
    def setup_method(self):
        self.client = make_client()
        self.old_etag = etag_of(self.client)
        self.response = patch(self.client, {"RequestedDeliveryDate": "2026-12-01"})

    def test_is_200_with_the_full_order_and_no_items(self):
        data = self.response.json()

        assert self.response.status_code == 200
        assert data["@odata.context"] == "$metadata#SalesOrder/$entity"
        assert data["SalesOrder"] == KEY
        assert data["RequestedDeliveryDate"] == "2026-12-01"
        assert "_Item" not in data

    def test_change_time_and_etag_move_on(self):
        data = self.response.json()

        assert data["LastChangeDateTime"] == "2026-10-27T09:15:30Z"
        assert data["@odata.etag"] != self.old_etag

    def test_a_later_read_shows_the_change(self):
        read = self.client.get(order_url()).json()

        assert read["RequestedDeliveryDate"] == "2026-12-01"
        assert read["@odata.etag"] == self.response.json()["@odata.etag"]

    def test_the_list_filters_on_the_new_date(self):
        rows = self.client.get(URL, params={"$filter": "RequestedDeliveryDate eq 2026-12-01"}).json()["value"]

        assert [row["SalesOrder"] for row in rows] == [KEY]

    def test_items_are_unchanged(self):
        items = self.client.get(order_url() + "/_Item").json()["value"]

        assert len(items) == len([o for o in ORDERS if o.sales_order == KEY][0].items)

    def test_the_old_etag_is_now_refused(self):
        response = self.client.patch(
            order_url(), json={"RequestedDeliveryDate": "2026-12-05"}, headers={"If-Match": self.old_etag}
        )

        assert response.status_code == 412

    def test_the_new_etag_works_even_within_the_same_second(self):
        newest = self.response.json()["@odata.etag"]

        response = self.client.patch(
            order_url(), json={"RequestedDeliveryDate": "2026-12-05"}, headers={"If-Match": newest}
        )

        assert response.status_code == 200
        assert response.json()["@odata.etag"] not in (newest, self.old_etag)


class TestChangeErrorsOverHttp:
    def test_missing_if_match_is_428(self):
        response = patch(make_client(), {"RequestedDeliveryDate": "2026-12-01"}, etag=None)

        assert response.status_code == 428
        assert response.json()["error"]["code"] == "ETAG_REQUIRED"
        assert response.json()["error"]["target"] == "SalesOrder"

    def test_stale_if_match_is_412_in_the_contract_shape(self):
        response = patch(make_client(), {"RequestedDeliveryDate": "2026-12-01"}, etag='W/"1"')

        assert response.status_code == 412
        assert response.json() == {
            "error": {
                "code": "ETAG_MISMATCH",
                "message": "The sales order was changed by someone else. Reload and try again.",
                "target": "SalesOrder",
            }
        }

    def test_unknown_order_is_404(self):
        response = patch(make_client(), {"RequestedDeliveryDate": "2026-12-01"}, key="0000099999", etag='W/"1"')

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "SALES_ORDER_NOT_FOUND"

    def test_completed_order_is_400_not_changeable(self):
        response = patch(make_client(), {"RequestedDeliveryDate": "2026-12-01"}, key=DONE)

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "VALIDATION_FAILED"
        assert response.json()["error"]["details"][0] == {
            "code": "ORDER_NOT_CHANGEABLE",
            "message": f"Sales order {DONE} has status C and cannot be changed.",
            "target": "SalesOrder",
        }

    def test_bad_date_is_400_with_details(self):
        response = patch(make_client(), {"RequestedDeliveryDate": "2020-01-01", "OverallStatus": "X"})

        details = response.json()["error"]["details"]
        assert response.status_code == 400
        assert [(d["code"], d["target"]) for d in details] == [
            ("FIELD_NOT_ALLOWED", "OverallStatus"),
            ("DELIVERY_DATE_IN_PAST", "RequestedDeliveryDate"),
        ]

    def test_a_refused_change_leaves_the_order_as_it_was(self):
        client = make_client()
        before = client.get(order_url()).json()
        patch(client, {"RequestedDeliveryDate": "2020-01-01"})

        assert client.get(order_url()).json() == before

    @pytest.mark.parametrize("content", [b"", b"nope", b"[]", b'"x"', b"null"])
    def test_body_that_is_not_an_object_is_400(self, content):
        client = make_client()
        response = client.patch(order_url(), content=content, headers={"If-Match": etag_of(client)})

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_REQUEST_BODY"

    def test_header_name_is_case_insensitive(self):
        client = make_client()
        response = client.patch(
            order_url(), content=json.dumps({"RequestedDeliveryDate": "2026-12-01"}), headers={"if-match": etag_of(client)}
        )

        assert response.status_code == 200


class TestCreateThenChangeFlow:
    def test_order_created_over_http_can_be_changed_with_the_etag_from_the_create(self):
        client = make_client()
        created = client.post(URL, json={
            "SalesOrderType": "OR", "SoldToParty": "0000100001", "TransactionCurrency": "INR",
            "_Item": [{"Material": "RM-1001", "Quantity": "5", "QuantityUnit": "KG"}],
        }).json()

        response = client.patch(
            order_url(created["SalesOrder"]),
            json={"RequestedDeliveryDate": "2026-11-20"},
            headers={"If-Match": created["@odata.etag"]},
        )

        assert response.status_code == 200
        assert response.json()["RequestedDeliveryDate"] == "2026-11-20"
        assert response.json()["LastChangeDateTime"] > created["LastChangeDateTime"]
