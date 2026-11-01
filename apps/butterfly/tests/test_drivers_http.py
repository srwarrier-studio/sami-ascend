import re
from pathlib import Path

import pytest

from butterfly.infrastructure.api.odata import DRIVERS_ROOT, ROOT
from butterfly.application.usecase.summarize_purchases_by_day import SummarizePurchasesByDay
from butterfly.application.usecase.summarize_purchases_by_material import SummarizePurchasesByMaterial
from butterfly.application.usecase.summarize_purchases_by_supplier import SummarizePurchasesBySupplier
from butterfly.infrastructure.memory.in_memory_driver_repo import InMemoryDriverRepo
from driver_data import COMPONENTS, CONTRACTS, DELIVERIES, PRODUCTION_ORDERS, make_driver_client

DRIVERS = InMemoryDriverRepo(deliveries=DELIVERIES)

CONTRACT = (Path(__file__).resolve().parents[3] / "docs/sap/drivers-contract.md").read_text()
FIELD_ROW = re.compile(r"^\| `(\w+)` \| `Edm\.\w+`", re.MULTILINE)

ENTITIES = {
    "SalesContract": (CONTRACTS, "SalesContract"),
    "PurchaseDelivery": (DELIVERIES, "PurchaseOrder"),
    "ProductionOrder": (PRODUCTION_ORDERS, "ProductionOrder"),
    "ProductionOrderComponent": (COMPONENTS, "ProductionOrder"),
    "PurchaseSummaryByDay": (SummarizePurchasesByDay(DRIVERS).execute(), "OrderDate"),
    "PurchaseSummaryBySupplier": (SummarizePurchasesBySupplier(DRIVERS).execute(), "Supplier"),
    "PurchaseSummaryByMaterial": (SummarizePurchasesByMaterial(DRIVERS).execute(), "Material"),
}


def contract_fields(entity: str) -> list[str]:
    start = CONTRACT.index(f"### {entity} (key")
    end = CONTRACT.index("\n##", start + 1)
    return FIELD_ROW.findall(CONTRACT[start:end])


def get(path: str):
    return make_driver_client().get(DRIVERS_ROOT + path)


class TestService:
    def test_the_root_is_the_one_in_the_contract(self):
        assert DRIVERS_ROOT == "/sap/opu/odata4/sap/zui_drivers_o4/srvd_a2x/sap/zdrivers/0001/"
        assert DRIVERS_ROOT in CONTRACT

    def test_it_does_not_share_a_root_with_the_sales_service(self):
        assert DRIVERS_ROOT != ROOT
        assert make_driver_client().get(ROOT + "SalesContract").status_code == 404

    def test_sales_still_work_next_to_it(self):
        assert make_driver_client().get(ROOT + "SalesOrder?$top=1").status_code == 200

    def test_an_empty_service_lists_nothing(self):
        from fastapi.testclient import TestClient
        from butterfly.entrypoint.app import create_app
        from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo

        body = TestClient(create_app(InMemorySalesOrderRepo([]))).get(DRIVERS_ROOT + "SalesContract?$count=true").json()
        assert body["value"] == [] and body["@odata.count"] == 0


@pytest.mark.parametrize("entity", ENTITIES)
class TestEveryEntity:
    def test_rows_have_exactly_the_contract_fields_in_order(self, entity):
        row = get(entity).json()["value"][0]
        assert list(row) == contract_fields(entity)

    def test_the_context_names_the_entity(self, entity):
        assert get(entity).json()["@odata.context"] == f"$metadata#{entity}"

    def test_lists_every_row_with_a_count_only_when_asked(self, entity):
        rows, _ = ENTITIES[entity]
        assert "@odata.count" not in get(entity).json()
        body = get(entity + "?$count=true").json()
        assert body["@odata.count"] == len(rows) == len(body["value"])

    def test_top_and_skip_page_through_the_rows_and_count_ignores_them(self, entity):
        rows, _ = ENTITIES[entity]
        first = get(entity + "?$top=1&$count=true").json()
        second = get(entity + "?$top=1&$skip=1").json()
        assert len(first["value"]) == 1 and first["@odata.count"] == len(rows)
        assert second["value"] != first["value"]

    def test_select_returns_the_chosen_fields_in_table_order(self, entity):
        wanted = contract_fields(entity)
        row = get(f"{entity}?$select={wanted[-1]},{wanted[0]}").json()["value"][0]
        assert list(row) == [wanted[0], wanted[-1]]

    def test_an_unknown_field_is_a_400(self, entity):
        response = get(f"{entity}?$select=Nope")
        assert response.status_code == 400 and response.json()["error"]["code"]

    @pytest.mark.parametrize("option", ["$expand=_Item", "$apply=groupby((Material))", "$search=steel", "$levels=2"])
    def test_options_the_contract_does_not_support_are_a_400(self, entity, option):
        response = get(f"{entity}?{option}")
        assert response.status_code == 400
        assert response.json()["error"]["code"] == "UNSUPPORTED_QUERY_OPTION"

    def test_writes_are_not_allowed(self, entity):
        client = make_driver_client()
        for send in (client.post, client.patch, client.put, client.delete):
            response = send(DRIVERS_ROOT + entity)
            assert response.status_code == 405
            assert response.json()["error"]["code"] == "METHOD_NOT_ALLOWED"

    def test_reading_one_row_by_key_is_not_supported(self, entity):
        _, key = ENTITIES[entity]
        assert get(f"{entity}('{key}')").status_code == 404


def ids(body, field):
    return [row[field] for row in body["value"]]


class TestSalesContract:
    def test_filter_by_customer_and_order_by_start_date(self):
        body = get("SalesContract?$filter=SoldToParty eq '0000100001'&$orderby=ValidFrom").json()
        assert ids(body, "SalesContract") == ["0040000071", "0040000127", "0040000163"]

    def test_filter_by_date_finds_the_contract_valid_on_a_day(self):
        body = get("SalesContract?$filter=ValidFrom le 2026-07-01 and ValidTo ge 2026-07-01&$orderby=SalesContract").json()
        assert ids(body, "SalesContract") == ["0040000127", "0040000140"]

    def test_filter_by_status(self):
        assert ids(get("SalesContract?$filter=ContractStatus eq 'A'&$orderby=SalesContract").json(), "SalesContract") == ["0040000140", "0040000163"]

    def test_filter_by_amount_uses_a_number_without_quotes(self):
        assert ids(get("SalesContract?$filter=ContractValue gt 9000000.00").json(), "SalesContract") == ["0040000163"]

    def test_amounts_and_dates_are_strings_in_the_contract_format(self):
        row = get("SalesContract?$filter=SalesContract eq '0040000127'").json()["value"][0]
        assert row["ContractValue"] == "9000000.00"
        assert row["ValidTo"] == "2026-07-12"

    def test_a_missing_predecessor_or_name_is_null_and_matches_no_comparison(self):
        body = get("SalesContract?$filter=SalesContract eq '0040000140'").json()
        assert body["value"][0]["PredecessorContract"] is None and body["value"][0]["CustomerName"] is None
        assert get("SalesContract?$filter=PredecessorContract eq '0040000071'").json()["value"][0]["SalesContract"] == "0040000127"
        assert ids(get("SalesContract?$filter=contains(CustomerName,'Acme')").json(), "SalesContract") == ["0040000071", "0040000127", "0040000163"]

    def test_order_by_puts_empty_values_first_when_ascending_and_last_when_descending(self):
        up = ids(get("SalesContract?$orderby=PredecessorContract").json(), "PredecessorContract")
        down = ids(get("SalesContract?$orderby=PredecessorContract desc").json(), "PredecessorContract")
        assert up[0] is None and down[-1] is None


class TestPurchaseDelivery:
    def test_filter_by_material_and_promised_date_range(self):
        url = "PurchaseDelivery?$filter=Material eq 'RAW-2002' and PromisedDeliveryDate ge 2026-07-01 and PromisedDeliveryDate le 2026-07-31"
        row = get(url).json()["value"][0]
        assert (row["PurchaseOrder"], row["SupplierName"]) == ("4500001207", "Doosan Metals Pvt Ltd")
        assert (row["PromisedDeliveryDate"], row["ActualDeliveryDate"], row["DeliveryStatus"]) == ("2026-07-14", "2026-07-26", "D")
        assert (row["OrderedQuantity"], row["DeliveredQuantity"]) == ("5000.000", "5000.000")

    def test_an_open_delivery_has_a_null_actual_date_that_matches_no_date_comparison(self):
        rows = get("PurchaseDelivery?$filter=DeliveryStatus eq 'O'").json()["value"]
        assert [r["ActualDeliveryDate"] for r in rows] == [None]
        assert get("PurchaseDelivery?$filter=ActualDeliveryDate ge 2000-01-01&$count=true").json()["@odata.count"] == 2

    def test_filter_by_supplier_and_order_by_promised_date_descending(self):
        body = get("PurchaseDelivery?$filter=Supplier eq '0000200001'&$orderby=PromisedDeliveryDate desc").json()
        assert ids(body, "PurchaseOrder") == ["4500001207", "4500001150"]

    def test_quantities_keep_three_decimals(self):
        row = get("PurchaseDelivery?$filter=PurchaseOrder eq '4500001302'").json()["value"][0]
        assert row["DeliveredQuantity"] == "0.000" and row["OrderedQuantity"] == "2000.000"


class TestProductionOrder:
    def test_filter_by_material_and_planned_end(self):
        body = get("ProductionOrder?$filter=Material eq 'RM-1002' and PlannedEndDate ge 2026-07-01&$orderby=PlannedEndDate").json()
        assert ids(body, "ProductionOrder") == ["0001000417", "0001000431"]

    def test_a_late_order_carries_its_actual_end_and_reason(self):
        row = get("ProductionOrder?$filter=ProductionOrder eq '0001000417'").json()["value"][0]
        assert (row["PlannedEndDate"], row["ActualEndDate"], row["DelayReason"], row["ProductionStatus"]) == ("2026-07-20", "2026-08-03", "MATERIAL_SHORTAGE", "C")

    def test_a_running_order_has_null_actual_end_and_reason(self):
        row = get("ProductionOrder?$filter=ProductionStatus eq 'R'").json()["value"][0]
        assert row["ActualEndDate"] is None and row["DelayReason"] is None

    def test_filter_by_delay_reason(self):
        assert ids(get("ProductionOrder?$filter=DelayReason eq 'MACHINE_BREAKDOWN'").json(), "ProductionOrder") == ["0001000388"]


class TestProductionOrderComponent:
    def test_filter_by_order(self):
        body = get("ProductionOrderComponent?$filter=ProductionOrder eq '0001000417'").json()
        assert body["value"] == [{"ProductionOrder": "0001000417", "Material": "RAW-2002", "MaterialDescription": "Steel coil", "RequiredQuantity": "4400.000", "QuantityUnit": "KG", "CompanyCode": "INA1"}]

    def test_filter_by_component_material_finds_every_order_using_it(self):
        body = get("ProductionOrderComponent?$filter=Material eq 'RAW-2002'&$orderby=ProductionOrder").json()
        assert ids(body, "ProductionOrder") == ["0001000417", "0001000431"]


class TestJoins:
    def test_a_late_order_leads_through_its_component_to_the_late_delivery(self):
        order = get("ProductionOrder?$filter=DelayReason eq 'MATERIAL_SHORTAGE'").json()["value"][0]
        component = get(f"ProductionOrderComponent?$filter=ProductionOrder eq '{order['ProductionOrder']}'").json()["value"][0]
        delivery = get(f"PurchaseDelivery?$filter=Material eq '{component['Material']}' and PromisedDeliveryDate le {order['PlannedEndDate']}&$orderby=PromisedDeliveryDate desc&$top=1").json()["value"][0]
        assert delivery["SupplierName"] == "Doosan Metals Pvt Ltd"
        assert delivery["ActualDeliveryDate"] > delivery["PromisedDeliveryDate"]
