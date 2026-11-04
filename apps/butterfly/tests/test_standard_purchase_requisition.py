import json
from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest
from conftest import ORDERS, NOW
from fastapi.testclient import TestClient

from butterfly.domain.entities.purchase_requisition import PurchaseRequisition, PurchaseRequisitionItem
from butterfly.entrypoint.app import create_app
from butterfly.infrastructure.api.standard.edmx import REQUISITION_METADATA, SPECS
from butterfly.infrastructure.api.standard.requisition import ROOT
from butterfly.infrastructure.memory.in_memory_purchase_requisition_repo import InMemoryPurchaseRequisitionRepo
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo

SAMPLES = SPECS / "api_purchaserequisition_2"
REAL_HEADER = json.loads((SAMPLES / "list-top2.json").read_text())["value"][0]
REAL_ITEM = json.loads((SAMPLES / "items-top2.json").read_text())["value"][0]
CREATED = datetime(2026, 11, 4, 10, 0, tzinfo=timezone.utc)


def item(number: str, line: str = "10", **changes) -> PurchaseRequisitionItem:
    base = PurchaseRequisitionItem(
        number, line, "MZ-TG-A11", "Lithium Ion Battery", "L001", Decimal("10.000"), "PC", Decimal("20.00"), "INR", "1010", "INA1", "1010", "002", date(2026, 12, 1)
    )
    return replace(base, **changes)


def requisition(number: str, *items: PurchaseRequisitionItem) -> PurchaseRequisition:
    return PurchaseRequisition(number, "NB", "", "purchase1", CREATED, CREATED, list(items))


@pytest.fixture(scope="module")
def client():
    repo = InMemoryPurchaseRequisitionRepo(
        [
            requisition("10000000", item("10000000", "10"), item("10000000", "20", release_status="03", processing_status="B", purchasing_document="4500000024", purchasing_document_item="10")),
            requisition("10000001", item("10000001", "10", plant="1020", release_status="02")),
        ]
    )
    return TestClient(create_app(InMemorySalesOrderRepo(ORDERS), requisitions=repo, now=lambda: NOW))


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
        assert get(client, "$metadata").content == REQUISITION_METADATA.read_bytes()


class TestARequisitionRow:
    def test_has_exactly_the_properties_of_the_real_header_row(self, client):
        row = get(client, "PurchaseReqn?$top=1").json()["value"][0]
        assert list(row) == list(REAL_HEADER)
        assert mismatched(row, REAL_HEADER) == []

    def test_an_item_has_exactly_the_properties_of_the_real_item_row(self, client):
        row = get(client, "PurchaseReqnItem?$top=1").json()["value"][0]
        assert list(row) == list(REAL_ITEM)
        assert mismatched(row, REAL_ITEM) == []

    def test_carries_the_stored_values_under_the_real_names(self, client):
        row = get(client, "PurchaseReqnItem(PurchaseRequisition='10000000',PurchaseRequisitionItem='20')").json()
        assert row["PurReqnReleaseStatus"] == "03" and row["ProcessingStatus"] == "B"
        assert row["PurchasingDocument"] == "4500000024" and row["PurchasingDocumentItem"] == "10"
        assert row["RequestedQuantity"] == 10 and row["BaseUnitISOCode"] == "PCE" and row["ItemNetAmount"] == 200
        assert row["CreatedByUser"] == "purchase1" and row["PurReqCreationDate"] == "2026-11-04"
        assert row["@odata.context"] == "$metadata#PurchaseReqnItem/$entity"

    def test_a_new_item_has_no_order_yet(self, client):
        row = get(client, "PurchaseReqnItem?$filter=PurchaseRequisition eq '10000001'").json()["value"][0]
        assert row["PurchasingDocument"] == "" and row["PurchasingDocumentItem"] == "0" and row["ReleaseIsNotCompleted"] is True


class TestReading:
    def test_the_list_has_the_odata_wrapper(self, client):
        body = get(client, "PurchaseReqn").json()
        assert body["@odata.context"] == "$metadata#PurchaseReqn" and "@odata.metadataEtag" in body and len(body["value"]) == 2

    def test_a_key_gets_one_requisition(self, client):
        body = get(client, "PurchaseReqn('10000001')").json()
        assert body["PurchaseRequisition"] == "10000001" and body["@odata.context"] == "$metadata#PurchaseReqn/$entity"

    def test_top_skip_and_count(self, client):
        body = get(client, "PurchaseReqnItem?$top=1&$skip=1&$count=true").json()
        assert body["@odata.count"] == 3 and len(body["value"]) == 1

    def test_filter_on_the_release_status(self, client):
        rows = get(client, "PurchaseReqnItem?$filter=PurReqnReleaseStatus eq '02'&$select=PurchaseRequisition,PurReqnReleaseStatus").json()["value"]
        assert [(r["PurchaseRequisition"], r["PurReqnReleaseStatus"]) for r in rows] == [("10000001", "02")]
        assert list(rows[0]) == ["@odata.etag", "PurchaseRequisition", "PurchaseRequisitionItem", "PurReqnReleaseStatus"]

    def test_orderby_descending(self, client):
        rows = get(client, "PurchaseReqn?$orderby=PurchaseRequisition desc").json()["value"]
        assert [r["PurchaseRequisition"] for r in rows] == ["10000001", "10000000"]

    def test_expand_the_items_of_a_requisition(self, client):
        body = get(client, "PurchaseReqn('10000000')?$expand=_PurchaseRequisitionItem($select=PurchaseRequisitionItem,PurReqnReleaseStatus)").json()
        assert [i["PurchaseRequisitionItem"] for i in body["_PurchaseRequisitionItem"]] == ["10", "20"]
        assert body["@odata.context"] == "$metadata#PurchaseReqn(_PurchaseRequisitionItem(PurchaseRequisitionItem,PurReqnReleaseStatus))/$entity"

    def test_expand_the_requisition_of_an_item(self, client):
        row = get(client, "PurchaseReqnItem?$expand=_PurReqn&$top=1").json()["value"][0]
        assert row["_PurReqn"]["PurchaseRequisition"] == "10000000"

    def test_items_of_one_requisition_by_navigation(self, client):
        assert len(get(client, "PurchaseReqn('10000000')/_PurchaseRequisitionItem").json()["value"]) == 2

    def test_count_segments_answer_plain_text(self, client):
        response = get(client, "PurchaseReqnItem/$count?$filter=Plant eq '1020'")
        assert response.text == "1" and response.headers["content-type"].startswith("text/plain")

    def test_the_other_entity_sets_are_empty(self, client):
        assert get(client, "PurchaseReqnAcctAssgmt").json()["value"] == []


def real_error(name: str) -> dict:
    return json.loads((SAMPLES / f"{name}.json").read_text())["error"]


class TestRefusalsLikeTheSandbox:
    @pytest.mark.parametrize(
        "path, status, sample",
        [
            ("PurchaseReqn('99999999')", 404, "error-not-found"),
            ("PurchaseReqn?$filter=Nope eq 1", 400, "error-bad-filter"),
            ("PurchaseReqn?$select=Nope", 400, "error-unknown-select"),
            ("PurchaseReqn?$foo=1", 400, "error-unknown-option"),
            ("PurchaseReqn?$top=abc", 400, "error-bad-top"),
            ("PurchaseReqnItem?$apply=groupby((PurchaseRequisitionType),aggregate($count as n))", 501, "error-apply-count-not-supported"),
        ],
    )
    def test_gives_the_status_code_and_message_of_the_sample(self, client, path, status, sample):
        response = get(client, path)
        error, real = response.json()["error"], real_error(sample)
        assert response.status_code == status
        assert (error["code"], error["message"], error["@SAP__common.ExceptionCategory"]) == (real["code"], real["message"], real["@SAP__common.ExceptionCategory"])
        assert error["innererror"]["ErrorDetails"]["@SAP__common.Application"] == real["innererror"]["ErrorDetails"]["@SAP__common.Application"]

    def test_a_wrong_expand_name_is_refused(self, client):
        error = get(client, "PurchaseReqn?$expand=_Item").json()["error"]
        assert error["code"].startswith("/IWCOR/CX_OD_EXPAND_ERROR") and "'_It...'" in error["message"]


TOMORROW = "2026-10-28"


def writable():
    repo = InMemoryPurchaseRequisitionRepo()
    return TestClient(create_app(InMemorySalesOrderRepo(ORDERS), requisitions=repo, now=lambda: NOW)), repo


def post(client, body):
    return client.post(f"{ROOT}/PurchaseReqn", json=body)


def valid_item(**changes):
    from butterfly.infrastructure.memory.in_memory_master_data_repo import InMemoryMasterDataRepo

    material = next(iter(InMemoryMasterDataRepo().materials.values()))
    base = {"Material": material.material_id, "Plant": {"INA1": "1000", "INA2": "2000", "INA3": "3000"}[material.company_code], "RequestedQuantity": 5, "BaseUnit": material.unit, "DeliveryDate": TOMORROW}
    return base | changes


class TestCreating:
    def test_returns_201_with_the_next_number_and_the_item_numbers(self):
        client, _ = writable()
        response = post(client, {"_PurchaseRequisitionItem": [valid_item(), valid_item()]})
        body = response.json()
        assert response.status_code == 201
        assert body["PurchaseRequisition"] == "10000000" and body["PurchaseRequisitionType"] == "NB"
        assert [i["PurchaseRequisitionItem"] for i in body["_PurchaseRequisitionItem"]] == ["10", "20"]
        assert response.headers["location"].endswith("/PurchaseReqn('10000000')")

    def test_the_second_requisition_gets_the_next_number(self):
        client, _ = writable()
        post(client, {"_PurchaseRequisitionItem": [valid_item()]})
        assert post(client, {"_PurchaseRequisitionItem": [valid_item()]}).json()["PurchaseRequisition"] == "10000001"

    def test_a_new_item_is_unordered_with_the_defaults(self):
        client, _ = writable()
        item = post(client, {"_PurchaseRequisitionItem": [valid_item()]}).json()["_PurchaseRequisitionItem"][0]
        assert item["ProcessingStatus"] == "N"
        assert item["PurchasingGroup"] == "001" and item["PurchasingOrganization"] and item["CompanyCode"] and item["PurReqnItemCurrency"] == "INR"
        assert item["CreatedByUser"] == "BUTTERFLY" and item["PurReqCreationDate"] == "2026-10-27" and item["ItemNetAmount"] > 0

    def test_the_created_requisition_can_be_read_back(self):
        client, _ = writable()
        post(client, {"_PurchaseRequisitionItem": [valid_item()]})
        assert get(client, "PurchaseReqnItem/$count").text == "1"


class TestCreateRefusals:
    @pytest.mark.parametrize(
        "item, code, target",
        [
            ({"Material": "NOPE"}, "MATERIAL_UNKNOWN", "Material"),
            ({"Plant": "9999"}, "PLANT_UNKNOWN", "Plant"),
            ({"RequestedQuantity": 0}, "QUANTITY_NOT_POSITIVE", "RequestedQuantity"),
            ({"RequestedQuantity": "abc"}, "FIELD_INVALID", "RequestedQuantity"),
            ({"DeliveryDate": "2026-10-01"}, "DELIVERY_DATE_IN_PAST", "DeliveryDate"),
            ({"BaseUnit": "XX"}, "UNIT_INVALID", "BaseUnit"),
            ({"Surprise": 1}, "FIELD_NOT_ALLOWED", "Surprise"),
        ],
    )
    def test_names_the_problem_and_the_field(self, item, code, target):
        client, repo = writable()
        response = post(client, {"_PurchaseRequisitionItem": [valid_item(**item)]})
        found = {(d["code"], d["target"].split("/")[-1]) for d in response.json()["error"]["details"]}
        assert response.status_code == 400 and (code, target) in found
        assert repo.list_all() == []

    @pytest.mark.parametrize("missing", ["Material", "Plant", "RequestedQuantity", "DeliveryDate"])
    def test_a_missing_required_field_is_refused(self, missing):
        client, _ = writable()
        item = {k: v for k, v in valid_item().items() if k != missing}
        details = post(client, {"_PurchaseRequisitionItem": [item]}).json()["error"]["details"]
        assert any(d["code"] == "FIELD_REQUIRED" and d["target"].endswith(missing) for d in details)

    def test_a_requisition_without_items_is_refused(self):
        client, _ = writable()
        assert post(client, {}).json()["error"]["details"][0]["code"] == "NO_ITEMS"

    def test_a_body_that_is_not_an_object_is_refused(self):
        client, _ = writable()
        assert client.post(f"{ROOT}/PurchaseReqn", content="[1]").status_code == 400


def stored(client):
    post(client, {"_PurchaseRequisitionItem": [valid_item(), valid_item()]})
    return get(client, "PurchaseReqn('10000000')").json()["@odata.etag"]


def change(client, etag, body, line="10"):
    headers = {} if etag is None else {"If-Match": etag}
    return client.patch(f"{ROOT}/PurchaseReqnItem(PurchaseRequisition='10000000',PurchaseRequisitionItem='{line}')", json=body, headers=headers)


class TestChangingAQuantity:
    def test_needs_the_quantity_and_the_iso_unit_together(self):
        client, _ = writable()
        etag = stored(client)
        item = get(client, "PurchaseReqnItem?$top=1").json()["value"][0]
        assert change(client, etag, {"RequestedQuantity": 7}).json()["error"]["details"][0]["target"] == "BaseUnitISOCode"
        done = change(client, etag, {"RequestedQuantity": 7, "BaseUnitISOCode": item["BaseUnitISOCode"]})
        assert done.status_code == 200 and done.json()["RequestedQuantity"] == 7

    def test_a_wrong_unit_or_quantity_is_refused(self):
        client, _ = writable()
        etag = stored(client)
        assert change(client, etag, {"RequestedQuantity": 7, "BaseUnitISOCode": "XXX"}).status_code == 400
        assert change(client, etag, {"RequestedQuantity": -1, "BaseUnitISOCode": get(client, "PurchaseReqnItem?$top=1").json()["value"][0]["BaseUnitISOCode"]}).status_code == 400

    def test_needs_the_etag_and_the_current_one(self):
        client, _ = writable()
        etag = stored(client)
        assert change(client, None, {}).status_code == 428
        assert change(client, 'W/"old"', {}).status_code == 412

    def test_an_item_that_is_released_is_refused(self):
        client, repo = writable()
        etag = stored(client)
        requisition = repo.get("10000000")
        requisition.items[0] = replace(requisition.items[0], release_status="03", release_codes=("01",))
        refused = change(client, etag, {"RequestedQuantity": 7, "BaseUnitISOCode": "PCE"})
        assert refused.status_code == 400 and refused.json()["error"]["details"][0]["code"] == "ITEM_NOT_CHANGEABLE"

    def test_an_item_that_is_ordered_is_refused(self):
        client, repo = writable()
        etag = stored(client)
        requisition = repo.get("10000000")
        requisition.items[0] = replace(requisition.items[0], processing_status="B", ordered_quantity=Decimal("5"))
        assert change(client, etag, {"RequestedQuantity": 7, "BaseUnitISOCode": "PCE"}).json()["error"]["details"][0]["code"] == "ITEM_NOT_CHANGEABLE"

    def test_an_unknown_item_is_404(self):
        client, _ = writable()
        etag = stored(client)
        assert change(client, etag, {}, line="90").status_code == 404


class TestDeletingAnItem:
    def test_marks_the_item_deleted(self):
        client, _ = writable()
        etag = stored(client)
        url = f"{ROOT}/PurchaseReqnItem(PurchaseRequisition='10000000',PurchaseRequisitionItem='10')"
        assert client.delete(url, headers={"If-Match": etag}).status_code == 204
        assert client.get(url).json()["IsDeleted"] is True

    def test_a_deleted_item_cannot_be_deleted_again(self):
        client, _ = writable()
        etag = stored(client)
        url = f"{ROOT}/PurchaseReqnItem(PurchaseRequisition='10000000',PurchaseRequisitionItem='10')"
        client.delete(url, headers={"If-Match": etag})
        new_etag = get(client, "PurchaseReqn('10000000')").json()["@odata.etag"]
        assert client.delete(url, headers={"If-Match": new_etag}).status_code == 400
