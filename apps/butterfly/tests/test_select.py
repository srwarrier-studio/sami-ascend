import pytest

from butterfly.infrastructure.api.odata import ROOT
from conftest import ORDERS, make_client

URL = ROOT + "SalesOrder"


def get(select):
    return make_client().get(URL, params={"$select": select})


class TestSelect:
    def test_returns_only_the_chosen_fields(self):
        rows = get("SalesOrder,CustomerName,TotalNetAmount").json()["value"]

        assert all(list(row) == ["SalesOrder", "CustomerName", "TotalNetAmount"] for row in rows)
        assert len(rows) == len(ORDERS)

    def test_context_lists_the_chosen_fields(self):
        context = get("SalesOrder,CustomerName,TotalNetAmount").json()["@odata.context"]

        assert context == "$metadata#SalesOrder(SalesOrder,CustomerName,TotalNetAmount)"

    def test_single_field(self):
        rows = get("OverallStatus").json()["value"]

        assert rows[0] == {"OverallStatus": ORDERS[0].overall_status}

    def test_output_follows_contract_field_order_not_request_order(self):
        row = get("TotalNetAmount,SalesOrder").json()["value"][0]

        assert list(row) == ["SalesOrder", "TotalNetAmount"]

    def test_spaces_around_commas_are_allowed(self):
        row = get("SalesOrder , CustomerName").json()["value"][0]

        assert list(row) == ["SalesOrder", "CustomerName"]

    def test_repeated_field_appears_once(self):
        row = get("SalesOrder,SalesOrder").json()["value"][0]

        assert list(row) == ["SalesOrder"]

    def test_values_keep_their_wire_format(self):
        row = get("TotalNetAmount,OrderDate,CreationDateTime").json()["value"][0]

        assert isinstance(row["TotalNetAmount"], str)
        assert row["CreationDateTime"].endswith("Z")

    def test_without_select_every_field_and_the_plain_context(self):
        body = make_client().get(URL).json()

        assert body["@odata.context"] == "$metadata#SalesOrder"
        assert len(body["value"][0]) == 12

    def test_works_together_with_filter(self):
        rows = make_client().get(
            URL, params={"$select": "SalesOrder", "$filter": "OverallStatus eq 'X'"}
        ).json()["value"]

        assert rows == [{"SalesOrder": o.sales_order} for o in ORDERS if o.overall_status == "X"]


class TestInvalidSelect:
    @pytest.mark.parametrize("text", ["Colour", "SalesOrder,Colour", "", ",", "SalesOrder,", "*"])
    def test_is_400_invalid_query_on_select(self, text):
        response = get(text)

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_QUERY"
        assert response.json()["error"]["target"] == "$select"

    def test_field_names_are_case_sensitive(self):
        assert get("salesorder").status_code == 400
