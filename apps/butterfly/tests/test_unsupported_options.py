import pytest

from butterfly.infrastructure.api.odata import ROOT
from conftest import make_client

URL = ROOT + "SalesOrder"


class TestUnsupportedQueryOption:
    @pytest.mark.parametrize("name", ["$apply", "$search", "$format", "$expand", "$levels"])
    def test_is_400_with_the_option_as_target(self, name):
        response = make_client().get(URL, params={name: "x"})

        assert response.status_code == 400
        assert response.json() == {
            "error": {
                "code": "UNSUPPORTED_QUERY_OPTION",
                "message": f"Query option {name} is not supported.",
                "target": name,
            }
        }

    def test_apply_message_matches_the_contract_example(self):
        response = make_client().get(URL, params={"$apply": "groupby((SoldToParty))"})

        assert response.json()["error"]["message"] == "Query option $apply is not supported."

    def test_supported_options_next_to_an_unsupported_one_still_fail(self):
        response = make_client().get(URL, params={"$top": "5", "$apply": "x"})

        assert response.status_code == 400

    def test_plain_parameters_without_dollar_are_ignored(self):
        assert make_client().get(URL, params={"sap-client": "100"}).status_code == 200


class TestLambdaFilter:
    @pytest.mark.parametrize(
        "text",
        [
            "_Item/any(i: i/Material eq 'RM-1001')",
            "_Item/all(i: i/Quantity gt 0)",
            "OverallStatus eq 'A' and _Item/any(i: i/Material eq 'RM-1001')",
        ],
    )
    def test_is_400_unsupported_on_filter(self, text):
        response = make_client().get(URL, params={"$filter": text})

        assert response.status_code == 400
        assert response.json()["error"]["code"] == "UNSUPPORTED_QUERY_OPTION"
        assert response.json()["error"]["target"] == "$filter"

    def test_any_inside_quoted_text_is_just_text(self):
        response = make_client().get(URL, params={"$filter": "CustomerName eq 'x/any(y)'"})

        assert response.status_code == 200
