from datetime import date

import httpx

from synapse_api.infrastructure.odata_reader import ODataReader
from synapse_api.infrastructure.registry_loader import load_registry
from synapse_api.infrastructure.registry_record_source import RegistryRecordSource
from synapse_api.infrastructure.settings import REGISTRY_PATH

REGISTRY = load_registry(REGISTRY_PATH)
ROOT = "http://sap/drivers/"


def run(record_name, key_field, key, end):
    seen = []

    def handler(request):
        seen.append(str(request.url))
        return httpx.Response(200, json={"value": [{"A": 1}]})

    source = RegistryRecordSource({"drivers": ODataReader(ROOT, 5, httpx.MockTransport(handler))})
    rows = source.rows(REGISTRY.records[record_name], key_field, key, end)
    return seen, rows


class TestRequests:
    def test_a_windowed_type_filters_on_the_key_and_the_near_side_of_the_window(self):
        seen, rows = run("purchase_delivery", "Material", "RAW-2002", date(2026, 7, 31))
        assert seen == [
            f"{ROOT}PurchaseDelivery?$filter=Material%20eq%20'RAW-2002'%20and%20PromisedDeliveryDate%20le%202026-07-31"
            "&$orderby=PromisedDeliveryDate,PurchaseOrder&$top=1000&$skip=0"
        ]
        assert rows == [{"A": 1}]

    def test_a_type_without_a_window_filters_on_the_key_only(self):
        seen, _ = run("production_component", "ProductionOrder", "0001000417", None)
        assert seen == [f"{ROOT}ProductionOrderComponent?$filter=ProductionOrder%20eq%20'0001000417'&$orderby=ProductionOrder,Material&$top=1000&$skip=0"]

    def test_the_contract_filters_on_the_start_of_its_validity(self):
        seen, _ = run("contract", "SoldToParty", "0000100001", date(2026, 8, 31))
        assert "ValidFrom%20le%202026-08-31" in seen[0] and seen[0].startswith(f"{ROOT}SalesContract?")
