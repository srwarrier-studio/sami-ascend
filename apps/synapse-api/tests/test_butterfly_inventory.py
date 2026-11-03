from datetime import date
from decimal import Decimal
from urllib.parse import unquote

import httpx
import pytest

from synapse_api.domain.errors import SapUnavailable
from synapse_api.infrastructure.butterfly_inventory_source import ButterflyInventorySource
from synapse_api.infrastructure.odata_reader import ODataReader

START, END = date(2026, 10, 1), date(2026, 10, 31)


def reader(handler) -> ODataReader:
    return ODataReader("http://sap/inventory/", 5, httpx.MockTransport(handler))


def seen(rows, urls):
    def handler(request):
        urls.append(unquote(str(request.url)))
        return httpx.Response(200, json={"value": rows})

    return handler


ITEM = {
    "Material": "RAW-2002", "MaterialDescription": None, "StockQuantity": "120.500", "QuantityUnit": "KG", "ReorderLevel": "400.000",
    "StockStatus": "L", "LastMovementDate": "2026-10-20", "Currency": "INR",
}


class TestSummaries:
    def test_status_summary_has_no_filter_without_a_company(self):
        urls = []
        row = {"StockStatus": "O", "StockValue": "100.00", "MaterialCount": 30, "Currency": "INR"}
        result = ButterflyInventorySource(reader(seen([row], urls))).stock_by_status()
        assert (result[0].status, result[0].value, result[0].count) == ("O", Decimal("100.00"), 30)
        assert urls[0].endswith("StockSummaryByStatus?$orderby=StockStatus,Currency,CompanyCode&$top=1000&$skip=0")

    def test_a_company_scope_becomes_a_filter(self):
        urls = []
        ButterflyInventorySource(reader(seen([], urls))).for_companies(("INA1", "INA2")).stock_by_group()
        assert "StockSummaryByMaterialGroup?$filter=(CompanyCode eq 'INA1' or CompanyCode eq 'INA2')&$orderby=MaterialGroup,Currency,CompanyCode" in urls[0]

    def test_warehouse_and_group_names_fall_back_to_their_codes(self):
        warehouse = {"Plant": "1000", "StorageLocation": "0001", "StorageLocationName": None, "StockValue": "5.00", "MaterialCount": 2, "Currency": "INR"}
        group = {"MaterialGroup": "BOTANIC", "MaterialGroupName": None, "StockValue": "5.00", "MaterialCount": 2, "Currency": "INR"}
        assert ButterflyInventorySource(reader(seen([warehouse], []))).stock_by_warehouse()[0].name == "0001"
        assert ButterflyInventorySource(reader(seen([group], []))).stock_by_group()[0].name == "BOTANIC"

    def test_month_values_ask_from_a_period(self):
        urls = []
        row = {"PostingPeriod": "2026-10", "StockValue": "9.00", "Currency": "INR"}
        result = ButterflyInventorySource(reader(seen([row], urls))).month_values("2026-05")
        assert result[0].period == "2026-10" and result[0].value == Decimal("9.00")
        assert "StockValueByMonth?$filter=PostingPeriod ge '2026-05'&$orderby=PostingPeriod,Currency,CompanyCode" in urls[0]

    def test_movement_days_and_hours_ask_for_the_range(self):
        urls = []
        day = {"PostingDate": "2026-10-02", "ReceiptValue": "10.00", "IssueValue": "4.00", "MovementCount": 3, "Currency": "INR"}
        hour = {"PostingDate": "2026-10-02", "PostingHour": 9, "MovementCount": 3}
        assert ButterflyInventorySource(reader(seen([day], urls))).movements_by_day(START, END)[0].issues == Decimal("4.00")
        assert ButterflyInventorySource(reader(seen([hour], urls))).movements_by_hour(START, END)[0].hour == 9
        assert "PostingDate ge 2026-10-01 and PostingDate le 2026-10-31" in urls[0] and "StockMovementSummaryByHour?" in urls[1]


class TestItems:
    def test_low_items_are_the_ones_not_ok(self):
        urls = []
        items = ButterflyInventorySource(reader(seen([ITEM], urls))).low_items()
        assert items[0].description == "RAW-2002" and items[0].last_movement == date(2026, 10, 20) and items[0].status == "L"
        assert "MaterialStock?$filter=StockStatus ne 'O'&$orderby=Material,Plant,StorageLocation" in urls[0]

    def test_idle_items_leave_out_zero_stock_and_take_the_oldest_first(self):
        urls = []
        ButterflyInventorySource(reader(seen([], urls))).idle_items(5)
        assert "StockStatus ne 'Z'&$orderby=LastMovementDate,Material,Plant,StorageLocation&$top=5" in urls[0]

    def test_an_item_never_moved_has_no_date(self):
        row = {**ITEM, "LastMovementDate": None}
        assert ButterflyInventorySource(reader(seen([row], []))).low_items()[0].last_movement is None

    def test_an_unreachable_service_is_unavailable(self):
        with pytest.raises(SapUnavailable):
            ButterflyInventorySource(reader(lambda request: httpx.Response(503))).low_items()
