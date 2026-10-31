import json

import pytest

from sami_agents.application.keyword_matcher import KeywordMatcher, stem, words
from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.entrypoint.evaluate import EVALS, load_cases, load_catalog
from sami_agents.infrastructure.alias_book import ALIASES_FILE, load_aliases
from sami_agents.infrastructure.mock_catalog_source import DEFAULT_ENTRIES

matcher = KeywordMatcher()


class TestStem:
    @pytest.mark.parametrize("word", ["purchase", "purchases", "purchasing", "purchased"])
    def test_forms_of_a_word_share_a_stem(self, word):
        assert stem(word) == "purchas"

    @pytest.mark.parametrize("pair", [("stopping", "stops"), ("customers", "customer"), ("sales", "sale"), ("orders", "ordering")])
    def test_other_endings_agree(self, pair):
        assert stem(pair[0]) == stem(pair[1])

    def test_short_words_are_left_alone(self):
        assert stem("bus") == "bus"
        assert stem("gas") == "gas"

    def test_filler_words_are_dropped_before_stemming(self):
        assert words("please show me the board") == set()


class TestRank:
    def test_matches_title_words(self):
        assert matcher.rank("show me top customers", DEFAULT_ENTRIES)[0] == "top-customers"

    def test_matches_description_words(self):
        assert matcher.rank("ranked", DEFAULT_ENTRIES)[:2] == ["top-customers", "top-materials"]

    def test_a_title_word_outranks_a_description_word(self):
        catalog = [CatalogEntry("a", "Weekly report", "Shows customers"), CatalogEntry("b", "Customers", "Anything")]
        assert matcher.rank("customers", catalog) == ["b", "a"]

    def test_the_best_match_comes_first_and_the_limit_holds(self):
        assert matcher.match("sales this month", DEFAULT_ENTRIES, 2)[0] == "sales-month"
        assert len(matcher.match("sales this month", DEFAULT_ENTRIES, 2)) == 2

    def test_ties_keep_catalog_order(self):
        catalog = [CatalogEntry("a", "Stock", ""), CatalogEntry("b", "Stock", "")]
        assert matcher.rank("stock", catalog) == ["a", "b"]

    def test_skips_the_given_ids(self):
        first = matcher.rank("sales", DEFAULT_ENTRIES)
        assert matcher.rank("sales", DEFAULT_ENTRIES, skip={first[0]}) == first[1:]

    def test_matches_other_forms_of_a_word(self):
        catalog = [CatalogEntry("pur", "Purchases this month", "")]
        assert matcher.rank("purchasing", catalog) == ["pur"]

    def test_ignores_filler_words(self):
        assert matcher.rank("please show me the", DEFAULT_ENTRIES) == []

    def test_no_match_is_empty(self):
        assert matcher.rank("weather in paris", DEFAULT_ENTRIES) == []


class TestAliases:
    catalog = [CatalogEntry("top-materials", "Top materials", "Ranked."), CatalogEntry("top-customers", "Top customers", "Ranked.")]

    def test_an_alias_matches_like_a_title_word(self):
        assert KeywordMatcher({"top-materials": ["products"]}).rank("which products", self.catalog) == ["top-materials"]

    def test_without_the_alias_nothing_matches(self):
        assert matcher.rank("which products", self.catalog) == []

    def test_an_alias_for_an_unknown_id_is_ignored(self):
        assert KeywordMatcher({"nope": ["products"]}).rank("products", self.catalog) == []

    def test_aliases_are_stemmed_too(self):
        assert KeywordMatcher({"top-materials": ["products"]}).rank("product", self.catalog) == ["top-materials"]


class TestAliasFile:
    def test_every_widget_in_the_catalog_snapshot_has_aliases_and_no_alias_is_for_an_unknown_widget(self):
        ids = {entry.id for entry in load_catalog(EVALS / "catalog.json")}
        aliases = load_aliases()
        assert set(aliases) == ids

    def test_the_file_is_a_map_of_ids_to_word_lists(self):
        assert all(words and all(isinstance(word, str) for word in words) for words in load_aliases().values())

    def test_a_malformed_file_is_refused(self, tmp_path):
        path = tmp_path / "aliases.json"
        path.write_text(json.dumps({"a": "not a list"}))
        with pytest.raises(ValueError, match="list of words"):
            load_aliases(path)

    def test_the_default_file_is_next_to_the_app(self):
        assert ALIASES_FILE.name == "aliases.json" and ALIASES_FILE.exists()


class TestEvaluationSets:
    def test_the_held_out_prompts_use_real_widget_ids(self):
        ids = {entry.id for entry in load_catalog(EVALS / "catalog.json")}
        for case in load_cases(EVALS / "heldout.json"):
            assert set(case.expected) <= ids, case.message

    def test_the_held_out_prompts_are_not_the_tuning_prompts(self):
        tuning = {case.message for case in load_cases(EVALS / "prompts.json")}
        assert not tuning & {case.message for case in load_cases(EVALS / "heldout.json")}

    def test_keywords_with_aliases_answer_the_prompts_they_were_tuned_for(self):
        catalog = load_catalog(EVALS / "catalog.json")
        keywords = KeywordMatcher(load_aliases())
        cases = load_cases(EVALS / "prompts.json") + load_cases(EVALS / "heldout.json")
        misses = [case.message for case in cases if case.expected and len(set(keywords.rank(case.message.removeprefix("@builder"), catalog)[:8]) & set(case.expected)) < case.minimum]
        assert misses == []
