from butterfly.infrastructure.api.odata import ROOT
from conftest import ORDERS, make_client

URL = ROOT + "SalesOrder"


class TestFilterOverHttp:
    def test_filters_the_list(self):
        body = make_client().get(URL, params={"$filter": "OverallStatus eq 'X'"}).json()

        assert [row["SalesOrder"] for row in body["value"]] == [
            order.sales_order for order in ORDERS if order.overall_status == "X"
        ]

    def test_url_encoded_filter_with_spaces_and_quotes(self):
        response = make_client().get(URL + "?$filter=OverallStatus%20eq%20%27A%27")

        assert response.status_code == 200
        assert {row["OverallStatus"] for row in response.json()["value"]} == {"A"}

    def test_no_match_is_200_with_an_empty_list(self):
        response = make_client().get(URL, params={"$filter": "OverallStatus eq 'Z'"})

        assert response.status_code == 200
        assert response.json()["value"] == []

    def test_keeps_seed_order(self):
        rows = make_client().get(URL, params={"$filter": "OverallStatus eq 'A'"}).json()["value"]

        keys = [row["SalesOrder"] for row in rows]
        assert keys == sorted(keys)


class TestInvalidFilterOverHttp:
    def test_unknown_field_is_400_in_the_error_format(self):
        response = make_client().get(URL, params={"$filter": "Colour eq 'red'"})

        assert response.status_code == 400
        assert response.json() == {
            "error": {
                "code": "INVALID_QUERY",
                "message": "Unknown field Colour in $filter.",
                "target": "$filter",
            }
        }

    def test_empty_filter_is_400(self):
        assert make_client().get(URL, params={"$filter": ""}).status_code == 400

    def test_malformed_filter_is_400_not_500(self):
        response = make_client().get(URL, params={"$filter": "((("})

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_QUERY"
