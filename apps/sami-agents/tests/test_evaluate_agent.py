import json
import threading

from sami_agents.application.evaluate_agent import EvalCase, EvaluateAgent, passes
from sami_agents.domain.errors import InvalidModelAnswer, ModelUnavailable
from sami_agents.entrypoint.evaluate import EVALS, describe, load_cases, load_catalog
from sami_agents.infrastructure.mock_catalog_source import DEFAULT_ENTRIES
from sami_agents.domain.gateways.chat_model import ChatModel
from sami_agents.infrastructure.mock_chat_model import MockChatModel

SALES = EvalCase("sales today", ["sales-today"])


def evaluate(case, picks=None, error=None):
    return EvaluateAgent(MockChatModel(picks, error), DEFAULT_ENTRIES).run(case)


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
    def test_a_model_that_picks_the_right_widget_passes_alone(self):
        result = evaluate(SALES, ["sales-today"])
        assert (result.status, result.model_pass, result.final_pass, result.picks) == ("ok", True, True, ["sales-today"])

    def test_a_model_that_misses_can_be_rescued_by_the_fallback(self):
        result = evaluate(SALES, ["day-sales"])
        assert (result.model_pass, result.final_pass) == (False, False)
        result = evaluate(EvalCase("top customers", ["top-customers"]), [])
        assert (result.model_pass, result.final_pass) == (False, True)

    def test_unknown_ids_do_not_count_as_picks(self):
        assert evaluate(SALES, ["nope", "sales-today", "sales-today"]).picks == ["sales-today"]

    def test_an_invalid_answer_is_recorded_and_the_fallback_answers(self):
        result = evaluate(EvalCase("top customers", ["top-customers"]), error=InvalidModelAnswer())
        assert (result.status, result.model_pass, result.final_pass) == ("invalid", False, True)

    def test_an_unavailable_model_is_recorded(self):
        assert evaluate(SALES, error=ModelUnavailable()).status == "unavailable"

    def test_times_each_answer(self):
        assert evaluate(SALES, ["sales-today"]).seconds >= 0


class MeetingModel(ChatModel):
    def __init__(self, people: int):
        self.meeting = threading.Barrier(people, timeout=5)

    def pick_widgets(self, message, catalog):
        self.meeting.wait()
        return ["sales-today"]


class TestParallel:
    def test_runs_the_batches_at_the_same_time(self):
        cases = [EvalCase(f"sales {n}", ["sales-today"]) for n in range(8)]
        results = EvaluateAgent(MeetingModel(4), DEFAULT_ENTRIES).execute(cases, parallel=4)
        assert len(results) == 8 and all(result.model_pass for result in results)

    def test_results_come_back_in_the_order_of_the_cases(self):
        cases = [EvalCase(f"case {n}", []) for n in range(7)]
        results = EvaluateAgent(MockChatModel(), DEFAULT_ENTRIES).execute(cases, parallel=3)
        assert [result.case.message for result in results] == [case.message for case in cases]

    def test_reports_each_result_as_it_finishes(self):
        seen = []
        EvaluateAgent(MockChatModel(), DEFAULT_ENTRIES).execute([EvalCase("a", []), EvalCase("b", [])], parallel=2, on_result=seen.append)
        assert sorted(result.case.message for result in seen) == ["a", "b"]

    def test_more_batches_than_cases_still_runs_every_case(self):
        results = EvaluateAgent(MockChatModel(), DEFAULT_ENTRIES).execute([EvalCase("a", []), EvalCase("b", [])], parallel=10)
        assert len(results) == 2

    def test_no_cases_gives_no_results(self):
        assert EvaluateAgent(MockChatModel(), DEFAULT_ENTRIES).execute([], parallel=4) == []


class TestSummary:
    def test_counts_and_times(self):
        agent = EvaluateAgent(MockChatModel(["sales-today"]), DEFAULT_ENTRIES)
        results = agent.execute([SALES, EvalCase("top customers", ["top-customers"]), EvalCase("weather", [])])
        summary = EvaluateAgent.summarise(results)
        assert summary.cases == 3
        assert summary.answered == 3
        assert summary.model_pass == 1
        assert summary.final_pass == 1
        assert summary.fallback == 0
        assert summary.slowest_seconds >= summary.average_seconds >= 0

    def test_an_empty_run_summarises_to_zeros(self):
        summary = EvaluateAgent.summarise([])
        assert (summary.cases, summary.average_seconds, summary.slowest_seconds) == (0, 0.0, 0.0)


class TestEvalData:
    def test_every_expected_id_is_in_the_catalog_snapshot(self):
        ids = {entry.id for entry in load_catalog(EVALS / "catalog.json")}
        for case in load_cases(EVALS / "prompts.json"):
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


class TestReport:
    def test_a_line_per_case_shows_the_verdict_and_what_was_expected(self):
        text = describe(evaluate(SALES, ["sales-today"]))
        assert text.startswith("[pass]")
        assert "sales today" in text and "expected ['sales-today']" in text
