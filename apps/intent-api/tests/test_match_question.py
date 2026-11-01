import pytest
from fakes import FakeClassifier

from intent_api.application.choose_scenarios import NOTHING, ChooseScenarios
from intent_api.application.match_question import MatchQuestion
from intent_api.application.read_domain import OTHER, ReadDomain
from intent_api.domain.entities.decision import Decision
from intent_api.domain.entities.match import NO_SCENARIOS, NOT_ABOUT_BUSINESS, NOT_SURE, NOTHING_MATCHED
from intent_api.domain.entities.scenario import Library, Scenario
from intent_api.domain.entities.selection import Selected
from intent_api.domain.errors import ClassifierUnavailable

DOMAINS = {"Sales": "sales", "Purchase": "spend", "Finance": "owed"}
LIBRARY = Library(
    DOMAINS,
    {
        "sales_value": Scenario("sales_value", "Sales", "the sales figure", ("a",), ("period",)),
        "sales_top": Scenario("sales_top", "Sales", "customers ranked", ("a",), ("period", "top")),
        "purchases_value": Scenario("purchases_value", "Purchase", "the purchases figure", ("a",), ("period",)),
    },
)


def domain(choice, probability, **scores):
    return Decision(choice, probability, {"Sales": 0.1, "Purchase": 0.1, "Finance": 0.1, OTHER: 0.1, **scores})


def matcher(by_text, min_probability=0.0) -> MatchQuestion:
    classifier = FakeClassifier(None, by_text)
    return MatchQuestion(ReadDomain(classifier, DOMAINS), ChooseScenarios(classifier, LIBRARY), LIBRARY, min_probability)


def scripted(*decisions) -> MatchQuestion:
    classifier = FakeClassifier()
    answers = iter(decisions)
    classifier.choose = lambda text, instructions, choices: next(answers)
    return MatchQuestion(ReadDomain(classifier, DOMAINS), ChooseScenarios(classifier, LIBRARY), LIBRARY)


class TestAnswered:
    def test_a_question_in_a_domain_selects_its_scenarios(self):
        match = scripted(domain("Sales", 0.9, Sales=0.9, Purchase=0.05), Decision("sales_value", 0.8)).execute("sales in august")
        assert match.answered
        assert (match.domain, match.domain_probability) == ("Sales", 0.9)
        assert match.selected == (Selected("sales_value", 0.8, "sales in august"),)
        assert match.offered == ("sales_value", "sales_top")
        assert match.domain_scores["Purchase"] == 0.05


class TestRefused:
    def test_other_is_not_about_the_business_with_the_two_nearest_domains(self):
        match = scripted(domain(OTHER, 0.6, Sales=0.2, Purchase=0.15, Finance=0.05)).execute("tell me a joke")
        assert (match.answered, match.reason, match.did_you_mean) == (False, NOT_ABOUT_BUSINESS, ("Sales", "Purchase"))
        assert match.selected == ()

    def test_a_domain_below_the_minimum_probability_is_not_sure(self):
        classifier = FakeClassifier()
        classifier.choose = lambda text, instructions, choices: domain("Sales", 0.4, Sales=0.4, Purchase=0.35)
        match = MatchQuestion(ReadDomain(classifier, DOMAINS), ChooseScenarios(classifier, LIBRARY), LIBRARY, 0.5).execute("revnue")
        assert (match.reason, match.did_you_mean) == (NOT_SURE, ("Sales", "Purchase"))

    def test_a_domain_without_scenarios_is_named_but_refused(self):
        match = scripted(domain("Finance", 0.9, Finance=0.9)).execute("who owes us money")
        assert (match.domain, match.reason, match.offered) == ("Finance", NO_SCENARIOS, ())

    def test_when_no_scenario_matches_the_offered_ones_are_listed(self):
        match = scripted(domain("Sales", 0.9, Sales=0.9), Decision(NOTHING, 0.8)).execute("sales")
        assert (match.reason, match.offered) == (NOTHING_MATCHED, ("sales_value", "sales_top"))

    def test_laya_down_is_not_swallowed(self):
        with pytest.raises(ClassifierUnavailable):
            matcher({}).execute("sales in august")
