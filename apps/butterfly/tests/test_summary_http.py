from butterfly.infrastructure.api.odata import ROOT
from conftest import ORDERS, make_client

DAY = ROOT + "SalesSummaryByDay"
CUSTOMER = ROOT + "SalesSummaryByCustomer"
MATERIAL = ROOT + "SalesSummaryByMaterial"
LIVE = [o for o in ORDERS if o.overall_status != "X"]


class TestSummaryShape:
    def test_day_rows_have_the_contract_fields(self):
        body = make_client().get(DAY).json()

        assert body["@odata.context"] == "$metadata#SalesSummaryByDay"
        assert list(body["value"][0]) == ["OrderDate", "TotalNetAmount", "OrderCount", "Currency"]

    def test_amounts_are_strings_and_counts_are_numbers(self):
        row = make_client().get(DAY).json()["value"][0]

        assert row["TotalNetAmount"].count(".") == 1
        assert isinstance(row["OrderCount"], int)

    def test_customer_and_material_rows_have_the_contract_fields(self):
        customer = make_client().get(CUSTOMER).json()["value"][0]
        material = make_client().get(MATERIAL).json()["value"][0]

        assert list(customer) == [
            "SoldToParty", "CustomerName", "OrderDate", "TotalNetAmount", "OrderCount", "Currency"
        ]
        assert list(material) == [
            "Material", "MaterialDescription", "OrderDate", "TotalQuantity",
            "QuantityUnit", "TotalNetAmount", "Currency",
        ]
        assert len(material["TotalQuantity"].split(".")[1]) == 3

    def test_default_order_is_oldest_date_first(self):
        dates = [r["OrderDate"] for r in make_client().get(CUSTOMER).json()["value"]]

        assert dates == sorted(dates)


class TestSummaryQueryOptions:
    def test_filter_by_date_range_and_orderby(self):
        days = sorted({o.order_date for o in LIVE})
        url = f"{DAY}?$filter=OrderDate ge {days[-2]} and OrderDate le {days[-1]}&$orderby=OrderDate desc"
        rows = make_client().get(url).json()["value"]

        assert [r["OrderDate"] for r in rows] == [days[-1].isoformat(), days[-2].isoformat()]

    def test_select_top_skip_and_count(self):
        body = make_client().get(DAY + "?$select=OrderCount&$top=2&$skip=1&$count=true").json()

        assert body["@odata.count"] == len({o.order_date for o in LIVE})
        assert len(body["value"]) == 2
        assert list(body["value"][0]) == ["OrderCount"]

    def test_filter_on_order_count(self):
        rows = make_client().get(DAY + "?$filter=OrderCount ge 1").json()["value"]

        assert rows

    def test_filter_on_text_field(self):
        rows = make_client().get(MATERIAL + "?$filter=startswith(Material,'RM-1001')").json()["value"]

        assert rows and all(r["Material"] == "RM-1001" for r in rows)


class TestSummaryErrors:
    def test_expand_is_unsupported(self):
        response = make_client().get(DAY + "?$expand=_Item")

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "UNSUPPORTED_QUERY_OPTION"

    def test_unknown_filter_field_is_invalid_query(self):
        response = make_client().get(DAY + "?$filter=Nope eq 1")

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_QUERY"

    def test_read_by_key_is_not_found(self):
        response = make_client().get(DAY + "('2026-10-27')")

        assert response.status_code == 404
        assert response.json()["error"]["code"] == "RESOURCE_NOT_FOUND"

    def test_writes_are_not_allowed(self):
        response = make_client().post(DAY, json={})

        assert response.status_code == 405
