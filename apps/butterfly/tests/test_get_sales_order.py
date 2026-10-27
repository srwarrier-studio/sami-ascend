from butterfly.infrastructure.api.odata import ROOT
from conftest import make_client


class TestGetSalesOrder:
    def test_returns_the_order_with_context_and_etag(self):
        body = make_client().get(ROOT + "SalesOrder('0000012002')").json()

        assert body["@odata.context"] == "$metadata#SalesOrder/$entity"
        assert body["@odata.etag"].startswith('W/"')
        assert body["SalesOrder"] == "0000012002"

    def test_url_encoded_quotes_work(self):
        response = make_client().get(ROOT + "SalesOrder(%270000012002%27)")

        assert response.status_code == 200

    def test_etag_comes_from_last_change_time(self):
        body = make_client().get(ROOT + "SalesOrder('0000012002')").json()

        stamp = body["LastChangeDateTime"].replace("-", "").replace(":", "")
        assert body["@odata.etag"] == 'W/"' + stamp.replace("T", "").rstrip("Z") + '"'

    def test_single_order_does_not_include_items(self):
        assert "_Item" not in make_client().get(ROOT + "SalesOrder('0000012002')").json()


class TestUnknownSalesOrder:
    def test_is_404_in_the_error_format(self):
        response = make_client().get(ROOT + "SalesOrder('0000099999')")

        assert response.status_code == 404
        assert response.json() == {
            "error": {
                "code": "SALES_ORDER_NOT_FOUND",
                "message": "Sales order 0000099999 does not exist.",
                "target": "SalesOrder",
            }
        }

    def test_key_without_leading_zeros_is_not_matched(self):
        assert make_client().get(ROOT + "SalesOrder('12001')").status_code == 404
