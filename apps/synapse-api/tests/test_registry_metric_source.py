from datetime import date
from decimal import Decimal

import httpx
import pytest
from structured_logging.request_id import request_id_var

from synapse_api.domain.errors import SapUnavailable
from synapse_api.infrastructure.butterfly_sales_source import ButterflySalesSource
from synapse_api.infrastructure.odata_reader import PAGE, ODataReader
from synapse_api.infrastructure.registry_loader import load_registry
from synapse_api.infrastructure.registry_metric_source import RegistryMetricSource
from synapse_api.infrastructure.settings import REGISTRY_PATH, Settings

START, END = date(2026, 10, 26), date(2026, 10, 27)
ROOT = "http://sap/root/"
REGISTRY = load_registry(REGISTRY_PATH)
SALES = REGISTRY.metrics["sales"]

DAY = {"OrderDate": "2026-10-26", "TotalNetAmount": "845000.00", "OrderCount": 14, "Currency": "INR"}
CUSTOMER = {"SoldToParty": "0000100001", "CustomerName": "Acme Industries", "OrderDate": "2026-10-27", "TotalNetAmount": "125000.00", "OrderCount": 2, "Currency": "INR"}
MATERIAL = {"Material": "RM-1001", "MaterialDescription": "Steel rod 12mm", "OrderDate": "2026-10-27", "TotalQuantity": "500.000", "QuantityUnit": "KG", "TotalNetAmount": "625000.00", "Currency": "INR"}


def source(handler, service="sales") -> RegistryMetricSource:
    return RegistryMetricSource({service: ODataReader(ROOT, 5, httpx.MockTransport(handler))})


def ok(*rows):
    return lambda request: httpx.Response(200, json={"value": list(rows)})


class TestRequestsMatchTheSalesSource:
    @pytest.mark.parametrize("dimension,method", [("day", "daily_sales"), ("customer", "customer_sales"), ("material", "material_sales")])
    def test_same_url_as_the_hand_written_source(self, dimension, method):
        old, new = [], []

        def record(into):
            def handler(request):
                into.append(str(request.url))
                return httpx.Response(200, json={"value": []})
            return handler

        getattr(ButterflySalesSource(Settings(sap_base_url=ROOT), httpx.MockTransport(record(old))), method)(START, END)
        source(record(new)).rows(SALES, dimension, START, END)
        assert new == old


class TestMapping:
    def test_day_rows_have_no_key_but_an_amount_and_a_count(self):
        [row] = source(ok(DAY)).rows(SALES, "day", START, END)
        assert (row.key, row.name, row.amount, row.count, row.quantity) == (None, "", Decimal("845000.00"), 14, None)
        assert str(row.amount) == "845000.00"

    def test_customer_rows_have_a_key_and_a_name(self):
        [row] = source(ok(CUSTOMER)).rows(SALES, "customer", START, END)
        assert (row.key, row.name, row.date, row.currency) == ("0000100001", "Acme Industries", date(2026, 10, 27), "INR")

    def test_material_rows_have_a_quantity_and_a_unit(self):
        [row] = source(ok(MATERIAL)).rows(SALES, "material", START, END)
        assert (row.quantity, row.unit, row.count) == (Decimal("500.000"), "KG", None)

    def test_a_null_name_becomes_empty_text(self):
        [row] = source(ok({**CUSTOMER, "CustomerName": None})).rows(SALES, "customer", START, END)
        assert row.name == ""


class TestAnotherMetricNeedsNoCode:
    TEXT = """
[metric.purchases]
label = "Purchases"
service = "drivers"
measure = "TotalNetAmount"
date = "OrderDate"
currency = "Currency"
by.day = { entity = "PurchaseSummaryByDay", order = "OrderDate,Currency" }
by.supplier = { entity = "PurchaseSummaryBySupplier", key = "Supplier", name = "SupplierName", order = "OrderDate,Supplier,Currency" }
"""

    def test_it_reads_from_its_service_and_entity(self, tmp_path):
        path = tmp_path / "r.toml"
        path.write_text(self.TEXT)
        purchases = load_registry(path).metrics["purchases"]
        seen = []

        def handler(request):
            seen.append(str(request.url))
            row = {"Supplier": "S1", "SupplierName": "Doosan", "OrderDate": "2026-10-26", "TotalNetAmount": "10.00", "Currency": "INR"}
            return httpx.Response(200, json={"value": [row]})

        [row] = source(handler, "drivers").rows(purchases, "supplier", START, END)
        assert seen[0].startswith(f"{ROOT}PurchaseSummaryBySupplier?$filter=OrderDate%20ge")
        assert (row.key, row.name, row.amount, row.count) == ("S1", "Doosan", Decimal("10.00"), None)


class TestPagingAndFailures:
    def test_every_page_is_read(self):
        seen = []

        def handler(request):
            skip = int(request.url.params["$skip"])
            seen.append(skip)
            return httpx.Response(200, json={"value": [DAY] * (PAGE if skip == 0 else 3)})

        assert len(source(handler).rows(SALES, "day", START, END)) == PAGE + 3
        assert seen == [0, PAGE]

    def test_a_failure_on_any_page_is_sap_unavailable(self):
        def handler(request):
            if int(request.url.params["$skip"]) == 0:
                return httpx.Response(200, json={"value": [DAY] * PAGE})
            return httpx.Response(500)

        with pytest.raises(SapUnavailable):
            source(handler).rows(SALES, "day", START, END)

    def test_the_request_id_is_sent(self):
        seen = []

        def handler(request):
            seen.append(request.headers.get("x-request-id"))
            return httpx.Response(200, json={"value": []})

        token = request_id_var.set("req-9")
        try:
            source(handler).rows(SALES, "day", START, END)
        finally:
            request_id_var.reset(token)
        assert seen == ["req-9"]
