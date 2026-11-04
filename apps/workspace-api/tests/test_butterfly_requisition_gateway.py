from datetime import date, datetime, timezone
from decimal import Decimal

import httpx
import pytest

pytest.importorskip("butterfly")
from fastapi.testclient import TestClient

from butterfly.entrypoint.app import create_app
from butterfly.infrastructure.memory.in_memory_master_data_repo import InMemoryMasterDataRepo
from butterfly.infrastructure.memory.in_memory_purchase_requisition_repo import InMemoryPurchaseRequisitionRepo
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo
from workspace_api.domain.entities.purchase_requisition import NewPurchaseRequisition, NewPurchaseRequisitionItem
from workspace_api.domain.errors import PurchaseRequisitionNotFound, PurchaseRequisitionRejected, SapNotReached
from workspace_api.infrastructure.butterfly_purchase_requisition_gateway import ButterflyPurchaseRequisitionGateway
from workspace_api.infrastructure.butterfly_requisition_mapper import target_from_json
from workspace_api.infrastructure.settings import Settings

NOW = datetime(2026, 11, 4, 9, 0, tzinfo=timezone.utc)
PLANTS = {"INA1": "1000", "INA2": "2000", "INA3": "3000"}
MASTER = InMemoryMasterDataRepo()
MATERIAL = next(iter(MASTER.materials.values()))
COMPANY = MATERIAL.company_code
OTHER_MATERIAL = next(m for m in MASTER.materials.values() if m.company_code != COMPANY)


class InProcessButterfly(httpx.BaseTransport):
    def __init__(self):
        self.butterfly = TestClient(create_app(InMemorySalesOrderRepo([]), requisitions=InMemoryPurchaseRequisitionRepo(), now=lambda: NOW))

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        answer = self.butterfly.request(request.method, str(request.url), content=request.content, headers=dict(request.headers))
        return httpx.Response(answer.status_code, content=answer.content, headers={"content-type": "application/json"})


class Unreachable(httpx.BaseTransport):
    def handle_request(self, request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("down")


def gateway(transport=None) -> ButterflyPurchaseRequisitionGateway:
    settings = Settings(sap_requisition_url="http://butterfly/sap/opu/odata4/sap/api_purchaserequisition_2/srvd_a2x/sap/purchaserequisition/0001/", sap_release_url="http://butterfly/butterfly/purchase-requisitions/")
    return ButterflyPurchaseRequisitionGateway(settings, transport or InProcessButterfly())


def item(material=MATERIAL, quantity="5", **changes) -> NewPurchaseRequisitionItem:
    base = NewPurchaseRequisitionItem(material.material_id, PLANTS[material.company_code], Decimal(quantity), material.unit, date(2026, 12, 1), "for the line")
    return NewPurchaseRequisitionItem(**{**base.__dict__, **changes})


def new(*items, description="Spare parts") -> NewPurchaseRequisition:
    return NewPurchaseRequisition(description, list(items))


class TestCreating:
    def test_returns_the_requisition_butterfly_numbered(self):
        created = gateway().create(new(item(), item()))
        assert created.purchase_requisition == "10000000" and created.description == "Spare parts"
        assert [i.item for i in created.items] == ["10", "20"]
        first = created.items[0]
        assert first.material == MATERIAL.material_id and first.company_code == COMPANY and str(first.quantity) == "5.000"
        assert len(str(first.net_amount).split(".")[1]) == 2
        assert first.text == "for the line" and first.delivery_date == date(2026, 12, 1) and first.net_amount > 0

    def test_the_status_comes_as_a_word_and_the_sap_code(self):
        first = gateway().create(new(item(quantity="1"))).items[0]
        assert (first.release_status, first.release_status_code, first.ordered, first.deleted) == ("released", "03", False, False)

    def test_a_requisition_that_needs_release_waits(self):
        expensive = new(item(quantity="5000000"))
        assert gateway().create(expensive).items[0].release_status == "not_released"

    def test_butterflys_refusal_names_the_field_workspace_uses(self):
        with pytest.raises(PurchaseRequisitionRejected) as refused:
            gateway().create(new(item(), item(material=MATERIAL.__class__("NOPE", "x", "PC", Decimal(1), COMPANY))))
        assert [(d.code, d.target) for d in refused.value.details] == [("MATERIAL_UNKNOWN", "items/1/material")]

    def test_butterfly_down_is_not_reached(self):
        with pytest.raises(SapNotReached):
            gateway(Unreachable()).create(new(item()))


class TestReading:
    def test_the_list_is_newest_first_with_the_total(self):
        service = gateway()
        for _ in range(3):
            service.create(new(item()))
        page = service.list_recent(2, 0, [COMPANY])
        assert [r.purchase_requisition for r in page.requisitions] == ["10000002", "10000001"] and page.total == 3
        assert [r.purchase_requisition for r in service.list_recent(2, 2, [COMPANY]).requisitions] == ["10000000"]

    def test_only_the_users_companies_are_listed(self):
        service = gateway()
        service.create(new(item()))
        service.create(new(item(OTHER_MATERIAL)))
        mine = service.list_recent(10, 0, [COMPANY])
        assert mine.total == 1 and mine.requisitions[0].items[0].company_code == COMPANY

    def test_one_requisition_is_read_by_number(self):
        service = gateway()
        service.create(new(item()))
        assert service.get("10000000").items[0].material == MATERIAL.material_id

    def test_an_unknown_number_is_not_found(self):
        with pytest.raises(PurchaseRequisitionNotFound):
            gateway().get("10000099")


class TestReleasing:
    def test_releases_step_by_step_and_returns_the_new_state(self):
        service = gateway()
        service.create(new(item(quantity="5000000")))
        assert service.release("10000000", "01", None).items[0].release_status == "in_release"
        assert service.release("10000000", "02", "10").items[0].release_status == "released"

    def test_refusals_come_back_as_details(self):
        service = gateway()
        service.create(new(item(quantity="5000000")))
        with pytest.raises(PurchaseRequisitionRejected) as refused:
            service.release("10000000", "02", None)
        assert refused.value.details[0].code == "RELEASE_REFUSED" and "not the next code" in refused.value.details[0].message

    def test_an_unknown_requisition_is_not_found(self):
        with pytest.raises(PurchaseRequisitionNotFound):
            gateway().release("10000099", "01", None)


class TestTargets:
    @pytest.mark.parametrize(
        "sap, ours",
        [
            ("_PurchaseRequisitionItem/0/Material", "items/0/material"),
            ("_PurchaseRequisitionItem/2/RequestedQuantity", "items/2/quantity"),
            ("_PurchaseRequisitionItem/1/DeliveryDate", "items/1/delivery_date"),
            ("_PurchaseRequisitionItem", "items"),
            ("PurReqnDescription", "description"),
            ("ReleaseCode", "release_code"),
        ],
    )
    def test_sap_targets_become_workspace_targets(self, sap, ours):
        assert target_from_json(sap) == ours
