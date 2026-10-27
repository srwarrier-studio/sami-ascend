import pytest

from butterfly.infrastructure.api.odata import ROOT
from conftest import ORDERS, make_client

URL = ROOT + "SalesOrder"


def get(**params):
    return make_client().get(URL, params={f"${name}": value for name, value in params.items()})


def keys(response):
    return [row["SalesOrder"] for row in response.json()["value"]]


ALL = [order.sales_order for order in ORDERS]


class TestTop:
    def test_limits_the_rows(self):
        assert keys(get(top="5")) == ALL[:5]

    def test_zero_returns_no_rows(self):
        assert keys(get(top="0")) == []

    def test_larger_than_the_data_returns_everything(self):
        assert keys(get(top="1000")) == ALL

    def test_default_is_100_rows(self):
        assert len(keys(get())) == len(ALL)

    def test_1000_is_allowed_and_1001_is_not(self):
        assert get(top="1000").status_code == 200
        assert get(top="1001").status_code == 400


class TestSkip:
    def test_skips_leading_rows(self):
        assert keys(get(skip="25")) == ALL[25:]

    def test_zero_skips_nothing(self):
        assert keys(get(skip="0")) == ALL

    def test_beyond_the_data_returns_no_rows(self):
        assert keys(get(skip="500")) == []

    def test_top_and_skip_make_pages(self):
        pages = keys(get(top="10", skip="0")) + keys(get(top="10", skip="10")) + keys(get(top="10", skip="20"))

        assert pages == ALL

    def test_last_page_is_shorter_than_top(self):
        assert len(keys(get(top="20", skip="20"))) == len(ALL) - 20


class TestCount:
    def test_true_adds_the_total(self):
        assert get(count="true").json()["@odata.count"] == len(ALL)

    def test_total_ignores_top_and_skip(self):
        body = get(count="true", top="5", skip="10").json()

        assert body["@odata.count"] == len(ALL)
        assert len(body["value"]) == 5

    def test_total_follows_the_filter(self):
        body = get(count="true", filter="OverallStatus eq 'X'", top="1").json()

        assert body["@odata.count"] == len([o for o in ORDERS if o.overall_status == "X"])
        assert len(body["value"]) == 1

    def test_total_is_zero_when_nothing_matches(self):
        body = get(count="true", filter="OverallStatus eq 'Z'").json()

        assert body["@odata.count"] == 0
        assert body["value"] == []

    def test_false_leaves_the_total_out(self):
        assert "@odata.count" not in get(count="false").json()

    def test_absent_leaves_the_total_out(self):
        assert "@odata.count" not in get().json()

    def test_total_comes_before_value_as_in_the_contract(self):
        assert list(get(count="true").json()) == ["@odata.context", "@odata.count", "value"]

    def test_no_next_link_even_when_more_rows_exist(self):
        assert "@odata.nextLink" not in get(top="5").json()


class TestInvalidPaging:
    @pytest.mark.parametrize("name", ["top", "skip"])
    @pytest.mark.parametrize("text", ["-1", "abc", "", "1.5", "1e2", " 5", "٣"])
    def test_not_a_whole_number_is_400(self, name, text):
        response = get(**{name: text})

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "INVALID_QUERY"
        assert response.json()["error"]["target"] == f"${name}"

    @pytest.mark.parametrize("text", ["yes", "TRUE", "1", ""])
    def test_count_other_than_true_or_false_is_400(self, text):
        response = get(count=text)

        assert response.status_code == 400
        assert response.json()["error"]["target"] == "$count"
