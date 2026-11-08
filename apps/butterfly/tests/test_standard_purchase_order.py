import json
from datetime import date, datetime
from decimal import Decimal

import pytest
from conftest import NOW, ORDERS
from fastapi.testclient import TestClient

from butterfly.domain.entities.drivers import PurchaseDelivery
from butterfly.domain.entities.purchase_order import PurchaseOrder, PurchaseOrderItem
from butterfly.entrypoint.app import create_app
from butterfly.infrastructure.api.standard.edmx import PURCHASE_ORDER_METADATA, SPECS
from butterfly.infrastructure.api.standard.purchase_order import ROOT
from butterfly.infrastructure.memory.in_memory_driver_repo import InMemoryDriverRepo
from butterfly.infrastructure.memory.in_memory_purchase_order_repo import InMemoryPurchaseOrderRepo
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo

SAMPLES = SPECS / "api_purchaseorder_2"
REAL_HEADER = json.loads((SAMPLES / "list-top2.json").read_text())["value"][0]
REAL_ITEM = json.loads((SAMPLES / "items-top2.json").read_text())["value"][0]
REAL_LINE = json.loads((SAMPLES / "schedule-lines-top2.json").read_text())["value"][0]
CREATED = datetime(2026, 11, 4, 10, 0)


def delivery(number: str, line: str, status: str = "O", delivered: str = "0") -> PurchaseDelivery:
    return PurchaseDelivery(
        number, line, "0000000123", "Herb Traders", "MZ-TG-A11", "Battery", date(2026, 11, 4), Decimal("10.000"), Decimal(delivered), "PC",
        date(2026, 12, 1), None, status, Decimal("200.00"), "INR", "INA1",
    )


@pytest.fixture(scope="module")
def client():
    drivers = InMemoryDriverRepo()
    repo = InMemoryPurchaseOrderRepo(drivers)
    items = [
        PurchaseOrderItem(delivery("4500000001", "00010", delivered="4.000"), "1010", "10000000", "00020"),
        PurchaseOrderItem(delivery("4500000001", "00020", status="X"), "1010"),
    ]
    repo.add(PurchaseOrder("4500000001", "NB", "INA1", "1010", "002", "0000000123", "INR", "purchase1", CREATED, CREATED, items))
    repo.add(PurchaseOrder("4500000002", "NB", "INA1", "1010", "002", "0000000123", "INR", "purchase1", CREATED, CREATED, [PurchaseOrderItem(delivery("4500000002", "00010"), "1010")]))
    return TestClient(create_app(InMemorySalesOrderRepo(ORDERS), drivers=drivers, purchase_orders=repo, now=lambda: NOW))


def kind(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def mismatched(actual: dict, real: dict) -> list[str]:
    return [name for name in real if real[name] is not None and actual[name] is not None and kind(actual[name]) != kind(real[name])]


def get(client, path):
    return client.get(f"{ROOT}/{path}")


class TestTheRealMetadata:
    def test_is_the_saved_real_document(self, client):
        assert get(client, "$metadata").content == PURCHASE_ORDER_METADATA.read_bytes()


class TestOrderRows:
    def test_a_header_row_has_exactly_the_properties_of_the_real_row(self, client):
        row = get(client, "PurchaseOrder?$top=1").json()["value"][0]
        assert list(row) == list(REAL_HEADER)
        assert mismatched(row, REAL_HEADER) == []

    def test_an_item_row_has_exactly_the_properties_of_the_real_row(self, client):
        row = get(client, "PurchaseOrderItem?$top=1").json()["value"][0]
        assert list(row) == list(REAL_ITEM)
        assert mismatched(row, REAL_ITEM) == []

    def test_a_schedule_line_row_has_exactly_the_properties_of_the_real_row(self, client):
        row = get(client, "PurchaseOrderScheduleLine?$top=1").json()["value"][0]
        assert list(row) == list(REAL_LINE)
        assert mismatched(row, REAL_LINE) == []

    def test_the_header_carries_the_stored_values(self, client):
        row = get(client, "PurchaseOrder('4500000001')").json()
        assert (row["Supplier"], row["CompanyCode"], row["DocumentCurrency"], row["CreatedByUser"]) == ("123", "INA1", "INR", "purchase1")

    def test_the_item_carries_the_values_and_the_requisition_link(self, client):
        row = get(client, "PurchaseOrderItem(PurchaseOrder='4500000001',PurchaseOrderItem='10')").json()
        assert (row["Material"], row["OrderQuantity"], row["NetAmount"], row["NetPriceAmount"]) == ("MZ-TG-A11", 10, 200, 20)
        assert (row["PurchaseRequisition"], row["PurchaseRequisitionItem"], row["Plant"]) == ("10000000", "20", "1010")

    def test_a_cancelled_item_has_the_deletion_code_and_no_open_quantity(self, client):
        item = get(client, "PurchaseOrderItem(PurchaseOrder='4500000001',PurchaseOrderItem='20')").json()
        line = get(client, "PurchaseOrderItem(PurchaseOrder='4500000001',PurchaseOrderItem='20')/_PurchaseOrderScheduleLineTP").json()["value"][0]
        assert (item["PurchasingDocumentDeletionCode"], line["OpenPurchaseOrderQuantity"]) == ("L", 0)

    def test_the_open_quantity_falls_by_what_was_received(self, client):
        line = get(client, "PurchaseOrderItem(PurchaseOrder='4500000001',PurchaseOrderItem='10')/_PurchaseOrderScheduleLineTP").json()["value"][0]
        assert (line["ScheduleLineOrderQuantity"], line["OpenPurchaseOrderQuantity"]) == (10, 6)


class TestQueryOptions:
    def test_filter_top_count_and_select(self, client):
        body = get(client, "PurchaseOrderItem?$filter=PurchaseOrder eq '4500000002'&$select=Material&$count=true").json()
        assert body["@odata.count"] == 1
        assert list(body["value"][0]) == ["PurchaseOrder", "PurchaseOrderItem", "Material"]

    def test_expand_gives_the_items_of_an_order(self, client):
        row = get(client, "PurchaseOrder('4500000001')?$expand=_PurchaseOrderItem").json()
        assert [i["PurchaseOrderItem"] for i in row["_PurchaseOrderItem"]] == ["10", "20"]

    def test_count_is_plain_text(self, client):
        assert get(client, "PurchaseOrder/$count").text == "2"

    def test_other_sets_answer_empty(self, client):
        assert get(client, "PurchaseOrderNote").json()["value"] == []


class TestRefusals:
    def test_unknown_order_is_not_found_like_sap(self, client):
        assert get(client, "PurchaseOrder('4599999999')").status_code == 404

    def test_a_bad_filter_is_refused(self, client):
        assert get(client, "PurchaseOrder?$filter=Nope eq 1").status_code == 400

    def test_an_unknown_select_is_refused(self, client):
        assert get(client, "PurchaseOrder?$select=Nope").status_code == 400
