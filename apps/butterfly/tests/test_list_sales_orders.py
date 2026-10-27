from butterfly.infrastructure.api.odata import ROOT
from conftest import ORDERS, make_client

URL = ROOT + "SalesOrder"
FIELDS = [
    "SalesOrder", "SalesOrderType", "SoldToParty", "CustomerName", "OrderDate",
    "RequestedDeliveryDate", "TransactionCurrency", "TotalNetAmount", "OverallStatus",
    "CreatedByUser", "CreationDateTime", "LastChangeDateTime",
]


class TestListSalesOrders:
    def test_returns_every_order_in_value(self):
        body = make_client().get(URL).json()

        assert body["@odata.context"] == "$metadata#SalesOrder"
        assert len(body["value"]) == len(ORDERS)

    def test_empty_store_returns_an_empty_value_list(self):
        assert make_client([]).get(URL).json()["value"] == []

    def test_no_count_next_link_or_etag_on_collections(self):
        body = make_client().get(URL).json()

        assert "@odata.count" not in body
        assert "@odata.nextLink" not in body
        assert "@odata.etag" not in body["value"][0]


class TestRowShape:
    def test_fields_are_in_contract_order(self):
        row = make_client().get(URL).json()["value"][0]

        assert list(row) == FIELDS

    def test_decimals_are_strings_with_two_places(self):
        row = make_client().get(URL).json()["value"][0]

        assert isinstance(row["TotalNetAmount"], str)
        assert len(row["TotalNetAmount"].split(".")[1]) == 2

    def test_timestamps_are_utc_with_z(self):
        row = make_client().get(URL).json()["value"][0]

        assert row["CreationDateTime"].endswith("Z")
        assert row["LastChangeDateTime"].endswith("Z")

    def test_dates_are_plain_iso_dates(self):
        row = make_client().get(URL).json()["value"][0]

        assert len(row["OrderDate"]) == 10

    def test_document_numbers_keep_leading_zeros(self):
        row = make_client().get(URL).json()["value"][0]

        assert row["SalesOrder"] == "0000012001"
        assert row["SoldToParty"] == "0000100001"

    def test_missing_requested_delivery_date_is_null(self):
        rows = make_client().get(URL).json()["value"]

        assert rows[0]["RequestedDeliveryDate"] is None
