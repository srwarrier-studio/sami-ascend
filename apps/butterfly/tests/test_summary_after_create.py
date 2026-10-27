from decimal import Decimal

from butterfly.infrastructure.api.odata import ROOT
from conftest import make_client

BODY = {
    "SalesOrderType": "OR",
    "SoldToParty": "0000100001",
    "TransactionCurrency": "INR",
    "_Item": [
        {"Material": "RM-1001", "Quantity": "50.000", "QuantityUnit": "KG"},
        {"Material": "RM-1005", "Quantity": "4", "QuantityUnit": "EA"},
    ],
}
TODAY = "2026-10-27"


def today_rows(client, entity, extra=""):
    params = {"$filter": f"OrderDate eq {TODAY}{extra}"}
    return client.get(ROOT + entity, params=params).json()["value"]


class TestSummaryAfterCreate:
    def setup_method(self):
        self.client = make_client()
        self.day_before = today_rows(self.client, "SalesSummaryByDay")[0]
        self.customer_before = today_rows(
            self.client, "SalesSummaryByCustomer", " and SoldToParty eq '0000100001'"
        )
        self.material_before = today_rows(self.client, "SalesSummaryByMaterial", " and Material eq 'RM-1001'")
        self.order = self.client.post(ROOT + "SalesOrder", json=BODY).json()

    def test_day_row_grows_by_the_new_order(self):
        after = today_rows(self.client, "SalesSummaryByDay")[0]

        assert after["OrderCount"] == self.day_before["OrderCount"] + 1
        assert Decimal(after["TotalNetAmount"]) == Decimal(self.day_before["TotalNetAmount"]) + Decimal(
            self.order["TotalNetAmount"]
        )

    def test_customer_row_grows_by_the_new_order(self):
        after = today_rows(self.client, "SalesSummaryByCustomer", " and SoldToParty eq '0000100001'")[0]
        before_count = self.customer_before[0]["OrderCount"] if self.customer_before else 0

        assert after["OrderCount"] == before_count + 1

    def test_material_row_grows_by_the_new_quantity(self):
        after = today_rows(self.client, "SalesSummaryByMaterial", " and Material eq 'RM-1001'")[0]
        before = Decimal(self.material_before[0]["TotalQuantity"]) if self.material_before else Decimal(0)

        assert Decimal(after["TotalQuantity"]) == before + Decimal("50.000")

    def test_changing_the_delivery_date_does_not_change_totals(self):
        key = self.order["SalesOrder"]
        self.client.patch(
            f"{ROOT}SalesOrder('{key}')",
            json={"RequestedDeliveryDate": "2030-01-15"},
            headers={"If-Match": self.order["@odata.etag"]},
        )

        assert today_rows(self.client, "SalesSummaryByDay")[0]["OrderCount"] == self.day_before["OrderCount"] + 1
