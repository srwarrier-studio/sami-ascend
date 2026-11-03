from datetime import date
from decimal import Decimal
from urllib.parse import unquote

import httpx
import pytest

from synapse_api.domain.errors import SapUnavailable
from synapse_api.infrastructure.butterfly_purchase_source import ButterflyPurchaseSource
from synapse_api.infrastructure.butterfly_receivables_source import ButterflyReceivablesSource
from synapse_api.infrastructure.odata_reader import ODataReader

ROOT = "http://sap/drivers/"
START, END = date(2026, 10, 1), date(2026, 10, 27)

ITEM = {
    "PurchaseOrder": "4500001207", "PurchaseOrderItem": "00010", "SupplierName": "Deccan Agro", "OrderDate": "2026-06-24",
    "PromisedDeliveryDate": "2026-07-14", "ActualDeliveryDate": None, "NetAmount": "260000.00", "NetAmountLocal": "260000.00", "LocalCurrency": "INR", "TransactionCurrency": "INR", "DeliveryStatus": "O",
}


def reader(handler) -> ODataReader:
    return ODataReader(ROOT, 5, httpx.MockTransport(handler))


def seen(rows, store):
    def handler(request):
        store.append(unquote(str(request.url)))
        return httpx.Response(200, json={"value": rows})

    return handler


class TestPurchases:
    def test_daily_purchases_ask_the_summary_for_the_range_and_company(self):
        urls = []
        row = {"OrderDate": "2026-10-02", "TotalNetAmount": "2163000.00", "TotalNetAmountLocal": "2163000.00", "LocalCurrency": "INR", "TotalNetAmountLocal": "2163000.00", "LocalCurrency": "INR", "OrderCount": 6, "Currency": "INR"}
        result = ButterflyPurchaseSource(reader(seen([row], urls))).for_companies(("INA1", "INA2")).daily_purchases(START, END)
        assert result[0].net_amount == Decimal("2163000.00") and result[0].order_count == 6
        assert "PurchaseSummaryByDay?$filter=OrderDate ge 2026-10-01 and OrderDate le 2026-10-27 and (CompanyCode eq 'INA1' or CompanyCode eq 'INA2')" in urls[0]
        assert "$orderby=OrderDate,Currency,CompanyCode" in urls[0]

    def test_supplier_purchases_read_the_supplier_summary(self):
        urls = []
        row = {"Supplier": "0000200001", "SupplierName": None, "OrderDate": "2026-10-02", "TotalNetAmount": "444000.00", "TotalNetAmountLocal": "444000.00", "LocalCurrency": "INR", "TotalNetAmountLocal": "444000.00", "LocalCurrency": "INR", "OrderCount": 2, "Currency": "INR"}
        result = ButterflyPurchaseSource(reader(seen([row], urls))).supplier_purchases(START, END)
        assert (result[0].supplier, result[0].name) == ("0000200001", "")
        assert "PurchaseSummaryBySupplier?" in urls[0] and "OrderDate,Supplier,Currency,CompanyCode" in urls[0]

    def test_group_purchases_read_the_material_group_summary(self):
        urls = []
        row = {"MaterialGroup": "BOTANIC", "MaterialGroupName": None, "OrderDate": "2026-10-02", "TotalNetAmount": "1949000.00", "TotalNetAmountLocal": "1949000.00", "LocalCurrency": "INR", "TotalNetAmountLocal": "1949000.00", "LocalCurrency": "INR", "OrderCount": 4, "Currency": "INR"}
        result = ButterflyPurchaseSource(reader(seen([row], urls))).for_companies(("INA1",)).group_purchases(START, END)
        assert (result[0].group, result[0].name, result[0].net_amount) == ("BOTANIC", "BOTANIC", Decimal("1949000.00"))
        assert "PurchaseSummaryByMaterialGroup?$filter=OrderDate ge 2026-10-01 and OrderDate le 2026-10-27 and (CompanyCode eq 'INA1')&$orderby=OrderDate,MaterialGroup,Currency,CompanyCode" in urls[0]

    def test_recent_items_leave_cancelled_out_and_take_the_latest(self):
        urls = []
        items = ButterflyPurchaseSource(reader(seen([ITEM], urls))).recent_items(5)
        assert items[0].actual is None and items[0].status == "O" and items[0].promised == date(2026, 7, 14)
        assert "DeliveryStatus ne 'X'" in urls[0] and "$orderby=OrderDate desc" in urls[0] and "$top=5" in urls[0]

    def test_items_due_filter_on_the_promised_date(self):
        urls = []
        ButterflyPurchaseSource(reader(seen([], urls))).items_due(START, END)
        assert "PromisedDeliveryDate ge 2026-10-01 and PromisedDeliveryDate le 2026-10-27 and DeliveryStatus ne 'X'" in urls[0]

    def test_open_item_count_uses_odata_count(self):
        urls = []

        def handler(request):
            urls.append(unquote(str(request.url)))
            return httpx.Response(200, json={"@odata.count": 36, "value": []})

        assert ButterflyPurchaseSource(reader(handler)).open_item_count() == 36
        assert "DeliveryStatus eq 'O'" in urls[0] and "$count=true" in urls[0] and "$top=0" in urls[0]

    def test_a_missing_count_is_unavailable(self):
        with pytest.raises(SapUnavailable):
            ButterflyPurchaseSource(reader(lambda request: httpx.Response(200, json={"value": []}))).open_item_count()

    def test_an_unreachable_service_is_unavailable(self):
        with pytest.raises(SapUnavailable):
            ButterflyPurchaseSource(reader(lambda request: httpx.Response(503))).daily_purchases(START, END)


class TestReceivables:
    TOTAL = {"AsOfDate": "2026-11-03", "Currency": "INR", "CompanyCode": "INA1", "OpenAmount": "1840000.00", "OverdueAmount": "450000.00", "OpenAmountLocal": "1840000.00", "OverdueAmountLocal": "450000.00", "LocalCurrency": "INR", "OpenCount": 12, "OverdueCount": 3}

    def test_totals_ask_for_the_day_and_company(self):
        urls = []
        result = ButterflyReceivablesSource(reader(seen([self.TOTAL], urls))).for_companies(("INA1",)).totals(date(2026, 11, 3))
        assert result[0].open_amount == Decimal("1840000.00") and result[0].overdue_count == 3
        assert "ReceivablesSummary?AsOfDate=2026-11-03&$filter=(CompanyCode eq 'INA1')&$orderby=AsOfDate,Currency,CompanyCode" in urls[0]

    def test_without_a_company_scope_there_is_no_filter(self):
        urls = []
        ButterflyReceivablesSource(reader(seen([], urls))).totals(date(2026, 11, 3))
        assert "$filter" not in urls[0]

    def test_by_customer_and_ageing_read_their_entities(self):
        urls = []
        customer = {"SoldToParty": "0000100001", "CustomerName": "Kestrel", "Currency": "INR", "OpenAmount": "10.00", "OverdueAmount": "5.00", "OpenAmountLocal": "10.00", "OverdueAmountLocal": "5.00", "LocalCurrency": "INR"}
        bucket = {"AgeBucket": "1-30", "Currency": "INR", "OpenAmount": "7.00", "OpenAmountLocal": "7.00", "LocalCurrency": "INR", "OpenCount": 2}
        source = ButterflyReceivablesSource(reader(seen([customer], urls)))
        assert source.by_customer(date(2026, 11, 3))[0].overdue_amount == Decimal("5.00")
        assert "ReceivablesByCustomer?" in urls[0]
        urls.clear()
        source = ButterflyReceivablesSource(reader(seen([bucket], urls)))
        assert source.ageing(date(2026, 11, 3))[0].bucket == "1-30"
        assert "ReceivablesAgeing?" in urls[0]


class TestCompanyCurrency:
    def test_purchase_rows_in_dollars_are_read_as_rupees(self):
        urls = []
        day = {"OrderDate": "2026-10-02", "TotalNetAmount": "100.00", "TotalNetAmountLocal": "8000.00", "LocalCurrency": "INR", "OrderCount": 1, "Currency": "USD"}
        result = ButterflyPurchaseSource(reader(seen([day], urls))).daily_purchases(START, END)
        assert (result[0].net_amount, result[0].currency) == (Decimal("8000.00"), "INR")
        item = {**ITEM, "NetAmount": "100.00", "NetAmountLocal": "8000.00", "LocalCurrency": "INR", "TransactionCurrency": "USD"}
        assert ButterflyPurchaseSource(reader(seen([item], urls))).recent_items(5)[0].net_amount == Decimal("8000.00")

    def test_receivables_in_dollars_are_read_as_rupees(self):
        total = {"AsOfDate": "2026-11-03", "Currency": "USD", "CompanyCode": "INA1", "OpenAmount": "100.00", "OverdueAmount": "40.00", "OpenAmountLocal": "8000.00", "OverdueAmountLocal": "3200.00", "LocalCurrency": "INR", "OpenCount": 1, "OverdueCount": 1}
        result = ButterflyReceivablesSource(reader(seen([total], []))).totals(date(2026, 11, 3))
        assert (result[0].currency, result[0].open_amount, result[0].overdue_amount) == ("INR", Decimal("8000.00"), Decimal("3200.00"))
