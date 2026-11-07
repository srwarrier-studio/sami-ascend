from dataclasses import replace
from decimal import Decimal

from test_standard_purchase_order_create import from_requisition, order_body, post, requisition_item, setup

from butterfly.infrastructure.api.odata import DRIVERS_ROOT
from butterfly.infrastructure.api.standard.purchase_order import ROOT

ITEM = "PurchaseOrderItem(PurchaseOrder='4500000001',PurchaseOrderItem='10')"
DELETE = {"PurchasingDocumentDeletionCode": "L"}


def order_with_item(**quantity):
    client, requisitions, orders, drivers = setup(requisition_item("10"))
    post(client, order_body(from_requisition(**quantity)))
    etag = client.get(f"{ROOT}/{ITEM}").headers["etag"]
    return client, requisitions, drivers, etag


def patch(client, etag, body=DELETE, path=ITEM):
    headers = {} if etag is None else {"If-Match": etag}
    return client.patch(f"{ROOT}/{path}", json=body, headers=headers)


def summary_amount(drivers):
    return sum(d.net_amount for d in drivers.deliveries() if d.delivery_status != "X")


class TestDeletingAnItem:
    def test_the_item_comes_back_deleted_with_a_new_etag(self):
        client, _, _, etag = order_with_item(OrderQuantity=4)
        response = patch(client, etag)
        assert response.status_code == 200
        assert response.json()["PurchasingDocumentDeletionCode"] == "L"
        assert response.headers["etag"] != etag

    def test_the_amount_leaves_the_purchase_figures(self):
        client, _, drivers, etag = order_with_item(OrderQuantity=4)
        assert summary_amount(drivers) == Decimal("5000.00")
        patch(client, etag)
        assert summary_amount(drivers) == 0

    def test_the_supplier_figures_synapse_reads_rise_on_create_and_fall_on_delete(self):
        client, _, _, etag = order_with_item(OrderQuantity=4)

        def total():
            rows = client.get(f"{DRIVERS_ROOT}PurchaseSummaryBySupplier").json()["value"]
            return sum(Decimal(str(r["TotalNetAmount"])) for r in rows)

        assert total() == Decimal("5000.00")
        patch(client, etag)
        assert total() == 0

    def test_the_requisition_item_is_open_again(self):
        client, requisitions, _, etag = order_with_item(OrderQuantity=10)
        patch(client, etag)
        item = requisitions.get("10000000").items[0]
        assert (item.processing_status, item.ordered_quantity, item.purchasing_document) == ("N", Decimal("0.000"), "")

    def test_a_part_order_leaves_the_rest_ordered(self):
        client, requisitions, *_ = setup(requisition_item("10"))
        post(client, order_body(from_requisition(OrderQuantity=4)))
        post(client, order_body(from_requisition(OrderQuantity=6)))
        etag = client.get(f"{ROOT}/{ITEM}").headers["etag"]
        patch(client, etag)
        item = requisitions.get("10000000").items[0]
        assert (item.processing_status, item.ordered_quantity) == ("B", Decimal("6.000"))

    def test_the_reopened_quantity_can_be_ordered_again(self):
        client, *_, etag = order_with_item(OrderQuantity=10)
        patch(client, etag)
        assert post(client, order_body(from_requisition())).status_code == 201


class TestRefusals:
    def test_no_if_match_gives_428(self):
        client, *_ , _ = order_with_item()
        assert patch(client, None).status_code == 428

    def test_a_stale_etag_gives_412(self):
        client, *_ = order_with_item()
        assert patch(client, 'W/"19990101000000"').status_code == 412

    def test_anything_but_the_deletion_code_is_refused(self):
        client, *_, etag = order_with_item()
        response = patch(client, etag, {"OrderQuantity": 1})
        assert response.status_code == 400 and response.json()["error"]["details"][0]["code"] == "CHANGE_NOT_SUPPORTED"

    def test_deleting_twice_is_refused(self):
        client, *_, etag = order_with_item()
        first = patch(client, etag)
        second = patch(client, first.headers["etag"])
        assert second.status_code == 400 and second.json()["error"]["details"][0]["code"] == "ITEM_ALREADY_DELETED"

    def test_a_received_item_cannot_be_deleted(self):
        client, _, drivers, etag = order_with_item()
        drivers.delivery_rows[0] = replace(drivers.delivery_rows[0], delivered_quantity=Decimal("1.000"))
        response = patch(client, etag)
        assert response.status_code == 400 and response.json()["error"]["details"][0]["code"] == "ITEM_RECEIVED"

    def test_an_unknown_item_is_not_found(self):
        client, *_, etag = order_with_item()
        assert patch(client, etag, path="PurchaseOrderItem(PurchaseOrder='4500000001',PurchaseOrderItem='90')").status_code == 404
