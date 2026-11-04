import pytest
from conftest import NOW, ORDERS
from fastapi.testclient import TestClient
from test_standard_purchase_requisition import ROOT, get, post, valid_item

from butterfly.domain.entities.release_rule import RELEASE_RULES
from butterfly.entrypoint.app import create_app
from butterfly.infrastructure.memory.in_memory_purchase_requisition_repo import InMemoryPurchaseRequisitionRepo
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo

RELEASE = "/butterfly/purchase-requisitions"
SMALL, MEDIUM, LARGE = 100, 30000, 300000


def fresh():
    return TestClient(create_app(InMemorySalesOrderRepo(ORDERS), requisitions=InMemoryPurchaseRequisitionRepo(), now=lambda: NOW))


def create(client, *prices):
    items = [valid_item(PurchaseRequisitionPrice=price) for price in prices]
    return post(client, {"_PurchaseRequisitionItem": items}).json()


def status_of(client, number="10000000"):
    rows = get(client, f"PurchaseReqnItem?$filter=PurchaseRequisition eq '{number}'&$select=PurReqnReleaseStatus,ReleaseIsNotCompleted").json()["value"]
    return [(r["PurReqnReleaseStatus"], r["ReleaseIsNotCompleted"]) for r in rows]


def release(client, code, number="10000000", **extra):
    return client.post(f"{RELEASE}/{number}/release", json={"ReleaseCode": code} | extra)


class TestReleaseOnSave:
    def test_a_value_below_every_rule_is_released_when_saved(self):
        client = fresh()
        create(client, SMALL)
        assert status_of(client) == [("03", False)]

    def test_a_value_with_a_rule_waits_for_its_code(self):
        client = fresh()
        create(client, MEDIUM, LARGE)
        assert status_of(client) == [("01", True), ("01", True)]

    def test_each_item_follows_its_own_value(self):
        client = fresh()
        create(client, SMALL, MEDIUM)
        assert [s for s, _ in status_of(client)] == ["03", "01"]


class TestReleasingInOrder:
    def test_one_code_completes_a_one_step_strategy(self):
        client = fresh()
        create(client, MEDIUM)
        body = release(client, "01").json()
        assert body["items"][0]["PurReqnReleaseStatus"] == "03" and body["items"][0]["ReleaseIsNotCompleted"] is False

    def test_a_two_step_strategy_goes_through_release_in_progress(self):
        client = fresh()
        create(client, LARGE)
        assert release(client, "01").json()["items"][0]["PurReqnReleaseStatus"] == "02"
        assert status_of(client) == [("02", True)]
        assert release(client, "02").json()["items"][0]["PurReqnReleaseStatus"] == "03"

    def test_the_codes_must_come_in_order(self):
        client = fresh()
        create(client, LARGE)
        refused = release(client, "02")
        assert refused.status_code == 400 and "not the next code" in refused.json()["error"]["details"][0]["message"]
        assert status_of(client) == [("01", True)]

    def test_a_code_cannot_be_given_twice(self):
        client = fresh()
        create(client, LARGE)
        release(client, "01")
        assert "already given" in release(client, "01").json()["error"]["details"][0]["message"]

    def test_a_released_item_cannot_be_released_again(self):
        client = fresh()
        create(client, SMALL)
        assert release(client, "01").status_code == 400

    def test_one_named_item_is_released_alone(self):
        client = fresh()
        create(client, MEDIUM, MEDIUM)
        release(client, "01", PurchaseRequisitionItem="20")
        assert [s for s, _ in status_of(client)] == ["01", "03"]

    def test_without_an_item_every_item_waiting_for_that_code_moves(self):
        client = fresh()
        create(client, MEDIUM, LARGE, SMALL)
        release(client, "01")
        assert [s for s, _ in status_of(client)] == ["03", "02", "03"]

    def test_a_named_item_that_does_not_exist_is_404(self):
        client = fresh()
        create(client, MEDIUM)
        assert release(client, "01", PurchaseRequisitionItem="90").status_code == 404

    def test_an_unknown_requisition_is_404(self):
        assert release(fresh(), "01", number="10000099").status_code == 404

    @pytest.mark.parametrize("body", [{}, {"ReleaseCode": 1}, {"ReleaseCode": "01", "Extra": 1}])
    def test_a_bad_body_is_refused(self, body):
        client = fresh()
        create(client, MEDIUM)
        assert client.post(f"{RELEASE}/10000000/release", json=body).status_code == 400


class TestChangesAfterRelease:
    def test_an_item_in_release_cannot_change_its_quantity(self):
        client = fresh()
        create(client, LARGE)
        release(client, "01")
        etag = get(client, "PurchaseReqn('10000000')").json()["@odata.etag"]
        url = f"{ROOT}/PurchaseReqnItem(PurchaseRequisition='10000000',PurchaseRequisitionItem='10')"
        iso = get(client, "PurchaseReqnItem?$top=1").json()["value"][0]["BaseUnitISOCode"]
        refused = client.patch(url, json={"RequestedQuantity": 1, "BaseUnitISOCode": iso}, headers={"If-Match": etag})
        assert refused.json()["error"]["details"][0]["code"] == "ITEM_NOT_CHANGEABLE"

    def test_a_quantity_change_that_crosses_a_rule_changes_the_status(self):
        client = fresh()
        create(client, MEDIUM)
        assert status_of(client) == [("01", True)]
        etag = get(client, "PurchaseReqn('10000000')").json()["@odata.etag"]
        url = f"{ROOT}/PurchaseReqnItem(PurchaseRequisition='10000000',PurchaseRequisitionItem='10')"
        iso = get(client, "PurchaseReqnItem?$top=1").json()["value"][0]["BaseUnitISOCode"]
        client.patch(url, json={"RequestedQuantity": 1, "BaseUnitISOCode": iso}, headers={"If-Match": etag})
        assert status_of(client) == [("03", False)]


class TestTheRuleTable:
    def test_a_changed_table_changes_who_must_approve(self):
        from decimal import Decimal

        from butterfly.domain.entities.release_rule import ReleaseRule

        rules = (ReleaseRule("NB", "*", Decimal("0"), None, "09", ("07",), ("approver",)),)
        client = TestClient(create_app(InMemorySalesOrderRepo(ORDERS), requisitions=InMemoryPurchaseRequisitionRepo(), release_rules=rules, now=lambda: NOW))
        create(client, SMALL)
        assert status_of(client) == [("01", True)]
        assert release(client, "01").status_code == 400
        assert release(client, "07").json()["items"][0]["PurReqnReleaseStatus"] == "03"

    def test_the_standard_table_has_three_tiers(self):
        assert [len(rule.release_codes) for rule in RELEASE_RULES] == [0, 1, 2]
