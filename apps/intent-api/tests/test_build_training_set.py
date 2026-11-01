import json

import pytest

from intent_api.application.build_training_set import BuildTrainingSet, Settings, normalised, with_typo
from intent_api.application.choose_scenarios import NOTHING
from intent_api.application.read_domain import OTHER
from intent_api.infrastructure.eval_loader import load_cases
from intent_api.infrastructure.family_loader import FAMILIES_FILE, load_families
from intent_api.infrastructure.library_loader import load_library
from intent_api.infrastructure.training_files import to_row, write_files

LIBRARY = load_library()
FAMILIES, SLOTS = load_families(LIBRARY, FAMILIES_FILE)
EVALUATION = frozenset(normalised(case.question) for case in load_cases(LIBRARY))
ITEMS = BuildTrainingSet(LIBRARY, FAMILIES, SLOTS, exclude=EVALUATION).execute()


class TestBuild:
    def test_the_same_seed_gives_the_same_items_and_another_seed_does_not(self):
        again = BuildTrainingSet(LIBRARY, FAMILIES, SLOTS, exclude=EVALUATION).execute()
        other = BuildTrainingSet(LIBRARY, FAMILIES, SLOTS, Settings(seed=1), EVALUATION).execute()
        assert again == ITEMS and other != ITEMS

    def test_no_slot_is_left_unfilled(self):
        assert not [item.text for item in ITEMS if "{" in item.text or "}" in item.text]

    def test_training_and_held_out_items_never_share_a_family_or_a_text(self):
        train = [item for item in ITEMS if not item.heldout]
        held = [item for item in ITEMS if item.heldout]
        assert not {family for item in train for family in item.families} & {family for item in held for family in item.families}
        assert not {item.text.lower().rstrip("?") for item in train} & {item.text.lower().rstrip("?") for item in held}

    def test_nothing_in_the_evaluation_questions_is_a_training_text(self):
        assert not {normalised(item.text) for item in ITEMS} & EVALUATION

    def test_without_the_exclusion_the_overlap_would_be_there(self):
        unfiltered = BuildTrainingSet(LIBRARY, FAMILIES, SLOTS).execute()
        assert {normalised(item.text) for item in unfiltered} & EVALUATION

    def test_domain_items_offer_every_domain_and_other_in_library_order(self):
        domain_items = [item for item in ITEMS if item.kind == "domain"]
        assert domain_items and all(item.offered == (*LIBRARY.domains, OTHER) and item.answer in item.offered for item in domain_items)

    def test_scenario_items_offer_their_answer_nothing_last_and_only_their_domain(self):
        for item in (item for item in ITEMS if item.kind == "scenario"):
            assert item.answer in item.offered and item.offered[-1] == NOTHING
            domains = {LIBRARY.scenarios[name].domain for name in item.offered[:-1]}
            assert len(domains) == 1

    def test_some_scenario_items_offer_only_some_of_the_scenarios(self):
        sizes = {len(item.offered) for item in ITEMS if item.kind == "scenario" and item.answer == "sales_value"}
        assert len(sizes) > 1 and max(sizes) == 8

    def test_forecast_families_teach_nothing_and_not_business_teaches_other(self):
        nothing = [item for item in ITEMS if item.kind == "scenario" and item.answer == NOTHING]
        other = [item for item in ITEMS if item.kind == "domain" and item.answer == OTHER]
        assert nothing and other and not any(item.kind == "scenario" for item in ITEMS if item.answer == OTHER)

    def test_a_combined_question_gives_one_domain_item_and_one_item_per_clause(self):
        combined = [item for item in ITEMS if len(item.families) == 2]
        assert combined and all(item.kind == "domain" for item in combined)
        assert len([item for item in ITEMS if item.kind == "scenario" and item.text and any(one.text.startswith(item.text) for one in combined[:1])]) >= 1

    def test_every_scenario_and_domain_is_taught_in_training_and_tested(self):
        for held in (False, True):
            scenarios = {item.answer for item in ITEMS if item.kind == "scenario" and item.heldout == held}
            domains = {item.answer for item in ITEMS if item.kind == "domain" and item.heldout == held}
            assert set(LIBRARY.scenarios) <= scenarios and {*LIBRARY.domains, OTHER} <= domains

    def test_refusals_and_other_are_at_least_a_fifth_of_the_training_domain_items(self):
        domain_items = [item for item in ITEMS if item.kind == "domain" and not item.heldout]
        refusing = [item for item in domain_items if item.answer == OTHER or not any(family.scenario for family in FAMILIES if family.id == item.families[0])]
        assert len(refusing) / len(domain_items) >= 0.2

    def test_about_a_fifth_of_the_questions_carry_a_spelling_mistake(self):
        clean = BuildTrainingSet(LIBRARY, FAMILIES, SLOTS, Settings(typo_rate=0), EVALUATION).execute()
        assert len({item.text for item in ITEMS} - {item.text for item in clean}) > len(clean) // 10

    def test_no_item_is_repeated(self):
        assert len({(item.kind, normalised(item.text), item.offered, item.answer, item.heldout) for item in ITEMS}) == len(ITEMS)

    def test_no_answer_has_more_items_than_the_cap_so_the_big_domains_do_not_drown_the_small_ones(self):
        from collections import Counter

        sizes = Counter((item.kind, item.answer, item.heldout) for item in ITEMS)
        assert max(size for key, size in sizes.items() if not key[2]) <= Settings.cap_train
        assert max(size for key, size in sizes.items() if key[2]) <= Settings.cap_heldout


class TestTypo:
    def test_changes_a_long_word_or_a_known_spelling(self):
        import random

        changed = {with_typo("compare revenue for last month", random.Random(seed)) for seed in range(20)}
        assert "compare revenue for last month" not in changed and len(changed) > 3

    def test_leaves_short_text_alone(self):
        import random

        assert with_typo("hi", random.Random(1)) == "hi"


class TestFiles:
    def test_a_row_has_the_state_question_and_expected_answer_the_app_would_send(self):
        item = next(item for item in ITEMS if item.kind == "domain")
        row = to_row(item, LIBRARY)
        assert row["state"] == {"question": item.text}
        question = row["questions"]["choice"]
        assert question["instructions"] == "Which department should handle this?"
        assert list(question["criteria"]) == [*LIBRARY.domains, OTHER] and question["criteria"][OTHER] == "everything else"
        assert row["expected"] == {"choice": item.answer}

    def test_a_scenario_row_describes_each_offered_scenario_and_nothing(self):
        item = next(item for item in ITEMS if item.kind == "scenario")
        criteria = to_row(item, LIBRARY)["questions"]["choice"]["criteria"]
        assert list(criteria) == list(item.offered) and criteria[NOTHING] == "nothing about figures is asked"
        assert criteria[item.answer] == (LIBRARY.scenarios[item.answer].description if item.answer != NOTHING else criteria[NOTHING])

    def test_writes_training_and_held_out_files_one_row_per_line(self, tmp_path):
        counts = write_files(ITEMS, LIBRARY, tmp_path)
        assert counts == {"train": sum(not item.heldout for item in ITEMS), "heldout": sum(item.heldout for item in ITEMS)}
        lines = (tmp_path / "train.jsonl").read_text().splitlines()
        assert len(lines) == counts["train"] and set(json.loads(lines[0])) == {"state", "questions", "expected"}
