import json
import threading

from sami_agents.application.evaluate_agent import EvalCase, EvaluateAgent, passes
from sami_agents.application.keyword_matcher import KeywordMatcher
from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.domain.gateways.relevance_checker import RelevanceChecker
from sami_agents.entrypoint.evaluate import EVALS, describe, load_cases, load_catalog
from sami_agents.infrastructure.alias_book import load_aliases
from sami_agents.infrastructure.mock_catalog_source import DEFAULT_ENTRIES
from sami_agents.infrastructure.mock_relevance_checker import MockRelevanceChecker

SALES = EvalCase("sales today", ["sales-today"])


def evaluate(case, checker=None):
    return EvaluateAgent(checker, DEFAULT_ENTRIES).run(case)


class TestPasses:
    def test_needs_the_minimum_number_of_expected_ids(self):
        case = EvalCase("x", ["a", "b", "c"], minimum=2)
        assert not passes(case, ["a"])
        assert passes(case, ["a", "c"])

    def test_extra_ids_do_not_fail_a_case(self):
        assert passes(EvalCase("x", ["a"]), ["z", "a"])

    def test_a_case_with_nothing_expected_passes_only_with_no_ids(self):
        assert passes(EvalCase("x", []), [])
        assert not passes(EvalCase("x", []), ["a"])


class TestRun:
    def test_reports_what_the_keywords_proposed_and_what_the_pipeline_kept(self):
        result = evaluate(EvalCase("sales", ["day-sales"], 1), MockRelevanceChecker({"sales-today": 0.0, "sales-month": 0.0}))
        assert result.proposed == ["sales-today", "sales-month", "day-sales", "top-customers"]
        assert result.final == ["day-sales", "top-customers", "top-materials"]
        assert result.rejected == ["sales-today", "sales-month"]
        assert result.checks == 5

    def test_the_check_can_rescue_a_case_the_keywords_alone_fail(self):
        checker = MockRelevanceChecker({"sales-today": 0.0, "sales-month": 0.0, "day-sales": 0.0, "top-customers": 0.0})
        result = evaluate(EvalCase("sales", ["top-materials"]), checker)
        assert result.proposed_pass is False and result.final_pass is True

    def test_the_proposals_use_the_larger_limit_for_boards(self):
        catalog = [CatalogEntry(f"w{n:02d}", f"Report {n:02d}", "") for n in range(30)]
        result = EvaluateAgent(None, catalog).run(EvalCase("@builder report", ["w00"]))
        assert len(result.proposed) == 15

    def test_without_a_checker_the_answer_is_unchecked(self):
        result = evaluate(SALES)
        assert result.unchecked is True and result.checks == 0 and result.final == result.proposed[:4]

    def test_times_each_answer(self):
        assert evaluate(SALES, MockRelevanceChecker()).seconds >= 0


class MeetingChecker(RelevanceChecker):
    def __init__(self, people: int):
        self.meeting = threading.Barrier(people, timeout=5)

    def check(self, message, entry):
        self.meeting.wait()
        return 1.0


class TestParallel:
    def test_runs_the_batches_at_the_same_time(self):
        cases = [EvalCase("sales today", ["sales-today"]) for _ in range(8)]
        results = EvaluateAgent(MeetingChecker(4), DEFAULT_ENTRIES).execute(cases, parallel=4)
        assert len(results) == 8 and all(result.final_pass for result in results)

    def test_results_come_back_in_the_order_of_the_cases(self):
        cases = [EvalCase(f"case {n}", []) for n in range(7)]
        results = EvaluateAgent(None, DEFAULT_ENTRIES).execute(cases, parallel=3)
        assert [result.case.message for result in results] == [case.message for case in cases]

    def test_reports_each_result_as_it_finishes(self):
        seen = []
        EvaluateAgent(None, DEFAULT_ENTRIES).execute([EvalCase("a", []), EvalCase("b", [])], parallel=2, on_result=seen.append)
        assert sorted(result.case.message for result in seen) == ["a", "b"]

    def test_more_batches_than_cases_still_runs_every_case(self):
        assert len(EvaluateAgent(None, DEFAULT_ENTRIES).execute([EvalCase("a", []), EvalCase("b", [])], parallel=10)) == 2

    def test_no_cases_gives_no_results(self):
        assert EvaluateAgent(None, DEFAULT_ENTRIES).execute([], parallel=4) == []


class TestSummary:
    def test_counts_and_times(self):
        agent = EvaluateAgent(MockRelevanceChecker(), DEFAULT_ENTRIES)
        summary = EvaluateAgent.summarise(agent.execute([SALES, EvalCase("top customers", ["top-customers"]), EvalCase("weather", [])]))
        assert summary.cases == 3
        assert summary.proposed_pass == 3 and summary.final_pass == 3
        assert summary.unchecked == 0
        assert summary.average_checks > 0
        assert summary.slowest_seconds >= summary.average_seconds >= 0

    def test_an_empty_run_summarises_to_zeros(self):
        summary = EvaluateAgent.summarise([])
        assert (summary.cases, summary.average_seconds, summary.slowest_seconds) == (0, 0.0, 0.0)


class TestEvalData:
    def test_every_expected_id_is_in_the_catalog_snapshot(self):
        ids = {entry.id for entry in load_catalog(EVALS / "catalog.json")}
        for name in ["prompts.json", "heldout.json"]:
            for case in load_cases(EVALS / name):
                assert set(case.expected) <= ids, case.message

    def test_has_questions_builder_requests_and_an_out_of_scope_prompt(self):
        cases = load_cases(EVALS / "prompts.json")
        assert len(cases) >= 20
        assert any(case.message.startswith("@builder") for case in cases)
        assert any(case.expected == [] for case in cases)

    def test_minimum_never_exceeds_what_is_expected(self):
        for case in load_cases(EVALS / "prompts.json"):
            assert case.minimum <= max(len(case.expected), 1)

    def test_the_prompt_file_is_plain_json(self):
        assert isinstance(json.loads((EVALS / "prompts.json").read_text()), list)

    def test_the_whole_pipeline_without_a_checker_matches_the_keyword_search(self):
        agent = EvaluateAgent(None, load_catalog(EVALS / "catalog.json"), KeywordMatcher(load_aliases()))
        summary = EvaluateAgent.summarise(agent.execute(load_cases(EVALS / "prompts.json")))
        assert summary.final_pass == summary.proposed_pass == summary.cases


class TestReport:
    def test_a_line_per_case_shows_the_verdict_what_was_expected_and_what_was_rejected(self):
        text = describe(evaluate(SALES, MockRelevanceChecker({"sales-month": 0.0})))
        assert text.startswith("[pass]")
        assert "sales today" in text and "expected ['sales-today']" in text and "rejected" in text
