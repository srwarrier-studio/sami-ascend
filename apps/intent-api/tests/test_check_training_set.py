from intent_api.application.build_training_set import BuildTrainingSet, normalised
from intent_api.application.check_training_set import CheckTrainingSet
from intent_api.application.choose_scenarios import NOTHING
from intent_api.application.read_domain import OTHER
from intent_api.domain.entities.training import Family, TrainingItem
from intent_api.infrastructure.eval_loader import load_cases
from intent_api.infrastructure.family_loader import FAMILIES_FILE, load_families
from intent_api.infrastructure.library_loader import load_library

LIBRARY = load_library()
FAMILIES, SLOTS = load_families(LIBRARY, FAMILIES_FILE)
EVALUATION = frozenset(normalised(case.question) for case in load_cases(LIBRARY))
ITEMS = BuildTrainingSet(LIBRARY, FAMILIES, SLOTS, exclude=EVALUATION).execute()
DOMAINS = (*LIBRARY.domains, OTHER)


def check(items=ITEMS, families=FAMILIES, evaluation=EVALUATION):
    return CheckTrainingSet(LIBRARY, families, items, evaluation).execute()


def item(kind="domain", text="sales in may", answer="Sales", offered=DOMAINS, families=("f_a",), heldout=False):
    return TrainingItem(kind, text, answer, offered, families, heldout)


def problems_with(*extra):
    return " | ".join(check([*ITEMS, *extra]).problems)


class TestShippedSet:
    def test_passes_with_a_summary(self):
        report = check()
        assert report.problems == []
        assert "training items" in report.lines[0] and any("exact duplicates: 0" in line for line in report.lines)


class TestRules:
    def test_a_family_in_both_training_and_held_out_is_a_problem(self):
        trained = next(entry for entry in ITEMS if not entry.heldout)
        assert "families in both" in problems_with(item(text="a brand new text", families=trained.families, heldout=True))

    def test_a_text_in_both_training_and_held_out_is_a_problem(self):
        trained = next(entry for entry in ITEMS if not entry.heldout)
        assert "texts in both training and held-out" in problems_with(item(text=trained.text, families=("only_held",), heldout=True))

    def test_a_text_that_is_an_evaluation_question_is_a_problem(self):
        leaked = next(iter(EVALUATION))
        assert "also evaluation questions" in problems_with(item(text=leaked.upper() + "?", families=("leak",)))

    def test_a_scenario_with_no_training_items_is_a_problem(self):
        remaining = [entry for entry in ITEMS if not (entry.kind == "scenario" and entry.answer == "sales_why" and not entry.heldout)]
        assert "training: no scenario items for ['sales_why']" in " | ".join(check(remaining).problems)

    def test_a_domain_with_no_held_out_items_is_a_problem(self):
        remaining = [entry for entry in ITEMS if not (entry.kind == "domain" and entry.answer == "Finance" and entry.heldout)]
        assert "held-out: no domain items for ['Finance']" in " | ".join(check(remaining).problems)

    def test_no_items_that_teach_nothing_is_a_problem(self):
        remaining = [entry for entry in ITEMS if entry.answer != NOTHING]
        assert "no items that teach 'nothing is asked'" in " | ".join(check(remaining).problems)

    def test_a_group_with_too_few_families_is_a_problem(self):
        few = [family for family in FAMILIES if family.id not in {"forecast_sales_c", "forecast_sales_d"}]
        assert "forecast Sales: only 2 families" in " | ".join(check(families=few).problems)

    def test_unbalanced_scenario_items_are_a_problem(self):
        flooded = [item("scenario", f"sales in month {number}", "sales_trend", ("sales_trend", NOTHING), ("flood",)) for number in range(900)]
        assert "scenario items are unbalanced" in problems_with(*flooded)

    def test_too_few_refusing_items_is_a_problem(self):
        kept = [entry for entry in ITEMS if entry.kind != "domain" or entry.answer in ("Sales", "Purchase")]
        assert "refusing domain items are only" in " | ".join(check(kept).problems)

    def test_exact_duplicates_are_a_problem(self):
        assert "exact duplicate items" in problems_with(*[item(text="same question", families=("dup",)) for _ in range(120)])

    def test_the_same_question_with_two_answers_is_a_problem(self):
        assert "two different answers" in problems_with(item(text="some odd question", answer="Sales", families=("a1",)), item(text="Some odd question?", answer="Purchase", families=("a2",)))
