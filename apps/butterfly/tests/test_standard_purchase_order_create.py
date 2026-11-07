from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal

from conftest import NOW, ORDERS
from fastapi.testclient import TestClient

from butterfly.domain.entities.purchase_requisition import PurchaseRequisition, PurchaseRequisitionItem
from butterfly.entrypoint.app import create_app
from butterfly.infrastructure.api.standard.purchase_order import ROOT
from butterfly.infrastructure.memory.in_memory_driver_repo import InMemoryDriverRepo
from butterfly.infrastructure.memory.in_memory_purchase_order_repo import InMemoryPurchaseOrderRepo
from butterfly.infrastructure.memory.in_memory_purchase_requisition_repo import InMemoryPurchaseRequisitionRepo
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo

CREATED = datetime(2026, 10, 20, 10, 0, tzinfo=timezone.utc)
SUPPLIER = "200001"


def requisition_item(line: str, **changes) -> PurchaseRequisitionItem:
    base = PurchaseRequisitionItem(
        "10000000", line, "RM-1001", "Ashwagandha root", "L001", Decimal("10.000"), "KG", Decimal("1250.00"), "INR", "1000", "INA1", "1010", "001",
        date(2026, 12, 1), release_status="03",
    )
    return replace(base, **changes)


def setup(*items: PurchaseRequisitionItem):
    drivers = InMemoryDriverRepo()
    requisitions = InMemoryPurchaseRequisitionRepo([PurchaseRequisition("10000000", "NB", "", "purchase1", CREATED, CREATED, list(items))])
    orders = InMemoryPurchaseOrderRepo(drivers)
    client = TestClient(create_app(InMemorySalesOrderRepo(ORDERS), drivers=drivers, requisitions=requisitions, purchase_orders=orders, now=lambda: NOW))
    return client, requisitions, orders, drivers


def post(client, body, **headers):
    return client.post(f"{ROOT}/PurchaseOrder", json=body, headers=headers)


def order_body(*items, **header):
    return {"CompanyCode": "INA1", "Supplier": SUPPLIER, "_PurchaseOrderItem": list(items)} | header


def from_requisition(line="10", **changes):
    return {"PurchaseRequisition": "10000000", "PurchaseRequisitionItem": line} | changes


def direct(**changes):
    return {"Material": "RM-1001", "Plant": "1000", "OrderQuantity": 4, "_PurchaseOrderScheduleLineTP": [{"ScheduleLineDeliveryDate": "2026-12-01"}]} | changes


def targets(response):
    return [(d["code"], d["target"]) for d in response.json()["error"]["details"]]


class TestCreatingFromARequisition:
    def test_returns_201_with_the_next_number_and_the_item(self):
        client, *_ = setup(requisition_item("10"))
        response = post(client, order_body(from_requisition(OrderQuantity=4)))
        body = response.json()
        assert response.status_code == 201
        assert (body["PurchaseOrder"], body["Supplier"], body["PurchasingOrganization"]) == ("4500000001", "200001", "1010")
        item = body["_PurchaseOrderItem"][0]
        assert (item["PurchaseOrderItem"], item["Material"], item["OrderQuantity"], item["NetAmount"], item["PurchaseRequisition"]) == ("10", "RM-1001", 4, 5000, "10000000")
        assert response.headers["location"].endswith("/PurchaseOrder('4500000001')")

    def test_the_quantity_defaults_to_the_open_quantity_and_the_price_to_the_requisition_price(self):
        client, *_ = setup(requisition_item("10"))
        item = post(client, order_body(from_requisition())).json()["_PurchaseOrderItem"][0]
        assert (item["OrderQuantity"], item["NetPriceAmount"], item["NetAmount"]) == (10, 1250, 12500)

    def test_the_stored_order_item_feeds_the_purchase_figures(self):
        client, _, _, drivers = setup(requisition_item("10"))
        post(client, order_body(from_requisition(OrderQuantity=4)))
        stored = drivers.deliveries()[0]
        assert (stored.supplier, stored.supplier_name, stored.net_amount, stored.delivery_status, stored.company_code) == ("0000200001", "Deccan Agro Growers Cooperative", Decimal("5000.00"), "O", "INA1")

    def test_the_requisition_item_becomes_ordered_with_the_order_number(self):
        client, requisitions, *_ = setup(requisition_item("10"))
        post(client, order_body(from_requisition(OrderQuantity=4)))
        item = requisitions.get("10000000").items[0]
        assert (item.processing_status, item.ordered_quantity, item.purchasing_document, item.purchasing_document_item) == ("B", Decimal("4.000"), "4500000001", "10")

    def test_the_rest_of_the_requisition_item_can_be_ordered_later(self):
        client, requisitions, *_ = setup(requisition_item("10"))
        post(client, order_body(from_requisition(OrderQuantity=4)))
        assert post(client, order_body(from_requisition(OrderQuantity=6))).status_code == 201
        assert requisitions.get("10000000").items[0].ordered_quantity == Decimal("10.000")

    def test_two_orders_get_two_numbers(self):
        client, *_ = setup(requisition_item("10"), requisition_item("20"))
        post(client, order_body(from_requisition("10")))
        assert post(client, order_body(from_requisition("20"))).json()["PurchaseOrder"] == "4500000002"


class TestCreatingWithoutARequisition:
    def test_a_direct_item_uses_the_material_price(self):
        client, *_ = setup()
        item = post(client, order_body(direct())).json()["_PurchaseOrderItem"][0]
        assert (item["NetPriceAmount"], item["NetAmount"], item["PurchaseRequisition"]) == (1250, 5000, "")

    def test_the_price_can_be_given(self):
        client, *_ = setup()
        assert post(client, order_body(direct(NetPriceAmount=1000))).json()["_PurchaseOrderItem"][0]["NetAmount"] == 4000


class TestRefusals:
    def refused(self, client, body, status=400):
        response = post(client, body)
        assert response.status_code == status
        return response

    def test_nothing_is_saved_when_one_item_is_wrong(self):
        client, requisitions, orders, drivers = setup(requisition_item("10"))
        self.refused(client, order_body(from_requisition("10"), direct(Plant="9999")))
        assert drivers.deliveries() == [] and requisitions.get("10000000").items[0].ordered_quantity == 0

    def test_missing_header_fields(self):
        client, *_ = setup()
        response = self.refused(client, {"_PurchaseOrderItem": [direct()]})
        assert targets(response) == [("FIELD_REQUIRED", "CompanyCode"), ("FIELD_REQUIRED", "Supplier")]

    def test_no_items(self):
        client, *_ = setup()
        assert targets(self.refused(client, order_body())) == [("NO_ITEMS", "_PurchaseOrderItem")]

    def test_unknown_supplier_and_supplier_of_another_company(self):
        client, *_ = setup()
        assert targets(self.refused(client, order_body(direct(), Supplier="999999"))) == [("SUPPLIER_UNKNOWN", "Supplier")]
        assert targets(self.refused(client, order_body(direct(), CompanyCode="INA2")))[0] == ("SUPPLIER_COMPANY", "Supplier")

    def test_unknown_material_and_plant_of_another_company(self):
        client, *_ = setup()
        assert targets(self.refused(client, order_body(direct(Material="NOPE")))) == [("MATERIAL_UNKNOWN", "_PurchaseOrderItem/0/Material")]
        assert targets(self.refused(client, order_body(direct(Plant="2000")))) == [("PLANT_COMPANY", "_PurchaseOrderItem/0/Plant")]

    def test_an_unreleased_requisition_item(self):
        client, *_ = setup(requisition_item("10", release_status="02"))
        assert targets(self.refused(client, order_body(from_requisition()))) == [("REQUISITION_ITEM_NOT_RELEASED", "_PurchaseOrderItem/0/PurchaseRequisition")]

    def test_a_deleted_requisition_item(self):
        client, *_ = setup(requisition_item("10", is_deleted=True))
        assert targets(self.refused(client, order_body(from_requisition())))[0][0] == "REQUISITION_ITEM_DELETED"

    def test_an_unknown_requisition_item(self):
        client, *_ = setup(requisition_item("10"))
        assert targets(self.refused(client, order_body(from_requisition("30"))))[0][0] == "REQUISITION_ITEM_UNKNOWN"

    def test_ordering_the_same_requisition_item_twice(self):
        client, *_ = setup(requisition_item("10"))
        post(client, order_body(from_requisition()))
        assert targets(self.refused(client, order_body(from_requisition())))[0][0] == "REQUISITION_ITEM_ORDERED"

    def test_more_than_the_open_quantity(self):
        client, *_ = setup(requisition_item("10"))
        assert targets(self.refused(client, order_body(from_requisition(OrderQuantity=11)))) == [("QUANTITY_ABOVE_OPEN", "_PurchaseOrderItem/0/OrderQuantity")]

    def test_two_items_of_one_order_cannot_together_exceed_the_open_quantity(self):
        client, *_ = setup(requisition_item("10"))
        assert targets(self.refused(client, order_body(from_requisition(OrderQuantity=6), from_requisition(OrderQuantity=6))))[0][0] == "QUANTITY_ABOVE_OPEN"

    def test_a_currency_different_from_the_requisition(self):
        client, *_ = setup(requisition_item("10"))
        assert targets(self.refused(client, order_body(from_requisition(), DocumentCurrency="USD")))[0][0] == "CURRENCY_MISMATCH"

    def test_a_material_that_differs_from_the_requisition_item(self):
        client, *_ = setup(requisition_item("10"))
        assert targets(self.refused(client, order_body(from_requisition(Material="RM-1002"))))[0][0] == "REQUISITION_MISMATCH"

    def test_quantity_and_date_and_fields(self):
        client, *_ = setup()
        assert targets(self.refused(client, order_body(direct(OrderQuantity=0)))) == [("QUANTITY_NOT_POSITIVE", "_PurchaseOrderItem/0/OrderQuantity")]
        past = direct(_PurchaseOrderScheduleLineTP=[{"ScheduleLineDeliveryDate": "2020-01-01"}])
        assert targets(self.refused(client, order_body(past)))[0][0] == "DELIVERY_DATE_IN_PAST"
        assert targets(self.refused(client, order_body(direct(Colour="red"))))[0] == ("FIELD_NOT_ALLOWED", "_PurchaseOrderItem/0/Colour")

    def test_a_body_that_is_not_an_object(self):
        client, *_ = setup()
        assert self.refused(client, [1]).json()["error"]["code"] == "VALIDATION_FAILED"


class TestRetrying:
    def test_the_same_idempotency_key_creates_one_order(self):
        client, _, _, drivers = setup(requisition_item("10"))
        first = post(client, order_body(from_requisition()), **{"Idempotency-Key": "k1"})
        second = post(client, order_body(from_requisition()), **{"Idempotency-Key": "k1"})
        assert first.json()["PurchaseOrder"] == second.json()["PurchaseOrder"] == "4500000001"
        assert len(drivers.deliveries()) == 1

    def test_a_different_key_creates_another_order(self):
        client, *_ = setup(requisition_item("10"), requisition_item("20"))
        post(client, order_body(from_requisition("10")), **{"Idempotency-Key": "k1"})
        assert post(client, order_body(from_requisition("20")), **{"Idempotency-Key": "k2"}).json()["PurchaseOrder"] == "4500000002"
