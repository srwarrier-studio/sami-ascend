from sami_agents.application.keyword_matcher import KeywordMatcher
from sami_agents.infrastructure.mock_catalog_source import DEFAULT_ENTRIES

matcher = KeywordMatcher()


class TestKeywordMatcher:
    def test_matches_title_words(self):
        assert matcher.match("show me top customers", DEFAULT_ENTRIES, 4)[0] == "top-customers"

    def test_matches_description_words(self):
        assert matcher.match("ranked by net sales", DEFAULT_ENTRIES, 4)[:2] == ["top-customers", "top-materials"]

    def test_best_match_comes_first_and_the_limit_holds(self):
        assert matcher.match("sales this month", DEFAULT_ENTRIES, 2) == ["sales-month", "top-customers"]

    def test_ignores_filler_words(self):
        assert matcher.match("please show me the", DEFAULT_ENTRIES, 4) == []

    def test_no_match_is_empty(self):
        assert matcher.match("weather in paris", DEFAULT_ENTRIES, 4) == []
