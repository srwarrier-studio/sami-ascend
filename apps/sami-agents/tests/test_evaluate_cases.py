import json
from datetime import date

from sami_agents.application.evaluate_cases import EvaluateCases, summarise
from sami_agents.application.question_reader import QuestionReader
from sami_agents.entrypoint.case_eval import EVALS, EVAL_TODAY
from sami_agents.infrastructure.understanding_loader import load_understanding

READER = QuestionReader(load_understanding())
TODAY = date(2026, 10, 31)


def judge(case):
    return EvaluateCases(READER, TODAY).judge(case)


class TestJudging:
    def test_an_answer_passes_when_intent_metric_direction_and_month_match(self):
        case = {"question": "why did sales fall in august", "outcome": "answer", "intent": "why", "metric": "sales", "direction": "fall", "month": "2026-08"}
        assert judge(case).passed
        assert not judge({**case, "month": "2026-07"}).passed
        assert not judge({**case, "direction": "rise"}).passed

    def test_a_figure_ignores_the_direction(self):
        case = {"question": "what were sales for august", "outcome": "answer", "intent": "figure", "metric": "sales", "month": "2026-08"}
        assert judge(case).passed

    def test_a_refusal_must_give_the_expected_reason(self):
        case = {"question": "why did sales fall this month", "outcome": "refuse", "problem": "not_finished"}
        assert judge(case).passed
        assert not judge({**case, "problem": "restricted"}).passed

    def test_a_question_for_the_widgets_or_unreadable_both_reach_the_planner(self):
        assert judge({"question": "show me top customers", "outcome": "widgets"}).passed
        assert judge({"question": "tell me a joke", "outcome": "refuse", "problem": "unreadable"}).passed

    def test_an_answer_to_a_question_that_should_be_refused_is_a_wrong_answer(self):
        verdict = judge({"question": "why did sales fall in august", "outcome": "refuse", "problem": "restricted"})
        assert (verdict.passed, verdict.wrong_answer) == (False, True)

    def test_the_summary_counts_answers_refusals_and_wrong_answers(self):
        cases = [
            {"question": "why did sales fall in august", "outcome": "answer", "intent": "why", "metric": "sales", "direction": "fall", "month": "2026-08"},
            {"question": "tell me a joke", "outcome": "refuse", "problem": "unreadable"},
            {"question": "why did sales fall in august", "outcome": "refuse", "problem": "restricted"},
        ]
        assert summarise(EvaluateCases(READER, TODAY).run(cases)) == {"cases": 3, "passed": 2, "answers_right": "1/1", "refusals_right": "1/2", "wrong_answers": 1}


class TestTheQuestionSets:
    def load(self, name):
        return json.loads((EVALS / name).read_text())

    def test_every_case_is_well_formed(self):
        for name in ("cases.json", "cases_heldout.json"):
            for case in self.load(name):
                assert case["outcome"] in {"answer", "widgets", "refuse"}
                if case["outcome"] == "answer":
                    assert {"intent", "metric", "month"} <= set(case) and (case["intent"] != "why" or "direction" in case)
                if case["outcome"] == "refuse":
                    assert case["problem"] in {"unreadable", "restricted", "not_one_month", "not_finished"}

    def test_the_held_out_questions_are_not_in_the_tuning_set(self):
        tuning = {case["question"].lower() for case in self.load("cases.json")}
        assert not tuning & {case["question"].lower() for case in self.load("cases_heldout.json")}

    def test_the_sets_are_read_as_of_the_eval_day(self):
        assert EVAL_TODAY == TODAY
