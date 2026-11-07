import pytest

from intent_api.application.read_qualifiers import ReadQualifiers
from intent_api.infrastructure.qualifier_words_loader import load_qualifier_words


def read(text):
    return ReadQualifiers(load_qualifier_words()).read(text)


class TestNamedThings:
    def test_a_capitalised_name_in_the_middle_of_a_question(self):
        assert read("sales to Nordhaven Pharma last month").names == ["Nordhaven Pharma"]

    def test_a_country_in_any_case(self):
        assert read("export sales to usa in q2").names == ["usa"]
        assert read("exports to Germany").names == ["Germany"]

    def test_a_company_marker(self):
        assert "m/s" in read("how much do we owe m/s kalpavruksha").names

    @pytest.mark.parametrize("text", ["What were sales for August?", "sales in March", "sales in FY 2025-26 in INR", "Why did sales drop in Augsut?", "sales for Sabinsa", "total receivables from us customers"])
    def test_ordinary_capitals_are_not_names(self, text):
        assert read(text).names == []


class TestUnits:
    @pytest.mark.parametrize("text", ["how many kg of curcumin did we sell", "sales in tonnes", "number of orders"])
    def test_quantities_are_found(self, text):
        assert read(text).quantities

    @pytest.mark.parametrize("text", ["sales in euros", "sales in GBP", "sales in €"])
    def test_other_currencies_are_found(self, text):
        assert read(text).currencies

    def test_rupees_and_dollars_are_fine(self):
        assert not read("sales in rupees or usd").refused


class TestTopN:
    @pytest.mark.parametrize("text, asked, shown", [("top 3 customers", 3, 3), ("top three customers", 3, 3), ("top 10 customers", 10, 10), ("top 50 customers", 50, 10)])
    def test_up_to_ten(self, text, asked, shown):
        found = read(text)
        assert (found.top_asked, found.top) == (asked, shown)

    def test_no_number_means_none(self):
        assert read("who are our top customers").top is None
