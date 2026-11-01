from fakes import FakeClassifier

from intent_api.application.choose_scenarios import NOTHING, ChooseScenarios
from intent_api.application.evaluate_matches import (
    CORRECTLY_REFUSED, EXACT, MISSING, WRONG_OR_EXTRA, WRONGLY_ANSWERED, WRONGLY_REFUSED,
    EvaluateMatches, describe, outcome_of, sweep_table,
)
from intent_api.application.match_question import MatchQuestion
from intent_api.application.read_domain import OTHER, ReadDomain
from intent_api.domain.entities.decision import Decision
from intent_api.domain.entities.eval_case import EvalCase
from intent_api.domain.entities.match import Match
from intent_api.domain.entities.scenario import Library, Scenario
from intent_api.domain.entities.selection import Selected

DOMAINS = {"Sales": "sales"}
LIBRARY = Library(DOMAINS, {
    "sales_value": Scenario("sales_value", "Sales", "the figure", ("a",)),
    "sales_top": Scenario("sales_top", "Sales", "customers ranked", ("a",)),
})


def case(question, scenarios, domain="Sales", id="q"):
    return EvalCase(id, question, "refuse" if not scenarios else "single", domain, frozenset(scenarios), False)


def match(*scenarios, reason=None):
    return Match("Sales", 0.9, {}, (), tuple(Selected(name, 0.8, "c") for name in scenarios), reason)


class TestOutcomeOf:
    def test_an_answer_with_exactly_the_expected_scenarios_is_exact(self):
        assert outcome_of(case("q", ["sales_value"]), match("sales_value")) == EXACT

    def test_part_of_the_expected_scenarios_is_missing(self):
        assert outcome_of(case("q", ["sales_value", "sales_top"]), match("sales_value")) == MISSING

    def test_an_unexpected_scenario_is_wrong_or_extra(self):
        assert outcome_of(case("q", ["sales_value"]), match("sales_top")) == WRONG_OR_EXTRA
        assert outcome_of(case("q", ["sales_value"]), match("sales_value", "sales_top")) == WRONG_OR_EXTRA

    def test_refusing_an_answerable_question_is_wrongly_refused(self):
        assert outcome_of(case("q", ["sales_value"]), match(reason="not_sure")) == WRONGLY_REFUSED

    def test_refusing_what_must_be_refused_is_correct_and_answering_it_is_not(self):
        assert outcome_of(case("q", []), match(reason="nothing_matched")) == CORRECTLY_REFUSED
        assert outcome_of(case("q", []), match("sales_value")) == WRONGLY_ANSWERED


def domain(choice, probability):
    return Decision(choice, probability, {"Sales": probability, OTHER: 1 - probability})


def scripted_evaluator() -> EvaluateMatches:
    domain_answers = {"figure": domain("Sales", 0.9), "ranking": domain("Sales", 0.4), "joke": domain(OTHER, 0.8), "forecast": domain("Sales", 0.7)}
    scenario_answers = {"figure": Decision("sales_value", 0.8), "ranking": Decision("sales_top", 0.5), "forecast": Decision("sales_value", 0.35)}

    class Classifier(FakeClassifier):
        def choose(self, text, instructions, choices):
            return (scenario_answers if NOTHING in choices else domain_answers)[text]

    classifier = Classifier()

    def build(domain_min, scenario_min):
        return MatchQuestion(ReadDomain(classifier, DOMAINS), ChooseScenarios(classifier, LIBRARY, 4, scenario_min), LIBRARY, domain_min)

    return EvaluateMatches(build)


CASES = [case("figure", ["sales_value"], id="a"), case("ranking", ["sales_top"], id="b"), case("joke", [], domain=OTHER, id="c"), case("forecast", [], id="d")]


class TestEvaluate:
    def test_counts_each_outcome_and_the_right_domains(self):
        score = scripted_evaluator().execute(CASES, 0.0, 0.0)
        assert score.counts == {EXACT: 2, CORRECTLY_REFUSED: 1, WRONGLY_ANSWERED: 1}
        assert (score.domain_right, score.domain_total, score.harmful) == (4, 4, 1)
        assert [failure.case.id for failure in score.failures] == ["d"]

    def test_thresholds_refuse_unsure_domains_and_scenarios(self):
        score = scripted_evaluator().execute(CASES, 0.5, 0.4)
        assert score.counts == {EXACT: 1, WRONGLY_REFUSED: 1, CORRECTLY_REFUSED: 2}
        assert score.harmful == 0

    def test_sweep_has_one_score_for_every_pair_of_thresholds(self):
        scores = scripted_evaluator().sweep(CASES, [0.0, 0.5], [0.0, 0.4, 0.6])
        assert [(s.domain_min, s.scenario_min) for s in scores] == [(0.0, 0.0), (0.0, 0.4), (0.0, 0.6), (0.5, 0.0), (0.5, 0.4), (0.5, 0.6)]


class TestReport:
    def test_describe_lists_the_numbers(self):
        text = describe(scripted_evaluator().execute(CASES, 0.0, 0.0))
        assert "answerable (2): exact 2" in text and "must refuse (2): correctly refused 1, wrongly answered 1" in text and "harmful (wrong or extra + wrongly answered) 1" in text

    def test_sweep_table_has_a_row_per_score(self):
        table = sweep_table(scripted_evaluator().sweep(CASES, [0.0], [0.0, 0.5]))
        assert len(table.splitlines()) == 3
