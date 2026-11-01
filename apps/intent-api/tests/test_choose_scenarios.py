import pytest
from fakes import FakeClassifier

from intent_api.application.choose_scenarios import NOTHING, QUESTION, ChooseScenarios, split_clauses
from intent_api.domain.entities.decision import Decision
from intent_api.domain.entities.scenario import Library, Scenario
from intent_api.domain.entities.selection import Selected
from intent_api.domain.errors import ClassifierUnavailable

LIBRARY = Library(
    {"Sales": "sales", "Purchase": "spend"},
    {
        "sales_value": Scenario("sales_value", "Sales", "the sales figure", ("a",), ("period",)),
        "sales_compare": Scenario("sales_compare", "Sales", "sales against the period before", ("a",), ("period",), ("sales_value",)),
        "sales_top": Scenario("sales_top", "Sales", "customers ranked", ("a",), ("period", "top")),
        "sales_why": Scenario("sales_why", "Sales", "why sales changed", ("a",), ("period",)),
        "purchases_value": Scenario("purchases_value", "Purchase", "the purchases figure", ("a",), ("period",)),
    },
)


def chooser(by_text, max_scenarios=4, min_probability=0.0, fallback=None) -> ChooseScenarios:
    return ChooseScenarios(FakeClassifier(fallback, by_text), LIBRARY, max_scenarios, min_probability)


class TestSplitClauses:
    @pytest.mark.parametrize("text, clauses", [
        ("sales in august", ["sales in august"]),
        ("sales of august and the largest customer", ["sales of august", "the largest customer"]),
        ("sales last month, purchases last month and the trend", ["sales last month", "purchases last month", "the trend"]),
        ("why did it fall; who is top then compare", ["why did it fall", "who is top", "compare"]),
        ("  ", []),
    ])
    def test_breaks_at_and_commas_semicolons_and_then(self, text, clauses):
        assert split_clauses(text) == clauses


class TestChoices:
    def test_offers_only_the_domain_scenarios_and_a_way_to_choose_nothing(self):
        classifier = FakeClassifier(Decision("sales_value", 0.9))
        ChooseScenarios(classifier, LIBRARY).execute("sales in august", "Sales")
        text, instructions, choices = classifier.calls[0]
        assert (text, instructions) == ("sales in august", QUESTION)
        assert list(choices) == ["sales_value", "sales_compare", "sales_top", "sales_why", NOTHING]
        assert choices["sales_top"] == "customers ranked"


class TestSelection:
    def test_one_clause_selects_its_scenario_with_the_probability(self):
        selected = chooser({"sales in august": Decision("sales_value", 0.9)}).execute("sales in august", "Sales")
        assert selected == [Selected("sales_value", 0.9, "sales in august")]

    def test_every_clause_can_select_a_scenario_best_first(self):
        by_text = {"compare sales": Decision("sales_compare", 0.6), "the top customer": Decision("sales_top", 0.8)}
        selected = chooser(by_text).execute("compare sales and the top customer", "Sales")
        assert [item.scenario for item in selected] == ["sales_top", "sales_compare"]

    def test_a_clause_that_asks_for_nothing_selects_nothing(self):
        by_text = {"sales in june": Decision("sales_value", 0.9), "july": Decision(NOTHING, 0.8)}
        assert [item.scenario for item in chooser(by_text).execute("sales in june, july", "Sales")] == ["sales_value"]

    def test_a_scenario_chosen_twice_keeps_its_best_probability(self):
        by_text = {"sales in june": Decision("sales_value", 0.5), "sales in july": Decision("sales_value", 0.9)}
        assert chooser(by_text).execute("sales in june and sales in july", "Sales") == [Selected("sales_value", 0.9, "sales in july")]

    def test_a_scenario_covered_by_another_is_dropped(self):
        by_text = {"sales in august": Decision("sales_value", 0.9), "compared to july": Decision("sales_compare", 0.7)}
        selected = chooser(by_text).execute("sales in august and compared to july", "Sales")
        assert [item.scenario for item in selected] == ["sales_compare"]

    def test_clauses_below_the_minimum_probability_are_ignored(self):
        by_text = {"sales in august": Decision("sales_value", 0.2)}
        assert chooser(by_text, min_probability=0.3).execute("sales in august", "Sales") == []

    def test_at_most_max_scenarios_are_kept_the_most_likely_first(self):
        by_text = {"a": Decision("sales_value", 0.5), "b": Decision("sales_top", 0.9), "c": Decision("sales_why", 0.7)}
        selected = chooser(by_text, max_scenarios=2).execute("a, b, c", "Sales")
        assert [item.scenario for item in selected] == ["sales_top", "sales_why"]

    def test_laya_down_is_not_swallowed(self):
        with pytest.raises(ClassifierUnavailable):
            chooser({}).execute("sales in august", "Sales")
