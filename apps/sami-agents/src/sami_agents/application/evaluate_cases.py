from dataclasses import dataclass
from datetime import date

PLANNER_PROBLEMS = {"widgets", "unreadable"}


@dataclass(frozen=True)
class Verdict:
    case: dict
    outcome: str
    problem: str | None
    got: dict
    passed: bool
    wrong_answer: bool


class EvaluateCases:
    def __init__(self, reader, today: date):
        self.reader = reader
        self.today = today

    def run(self, cases: list[dict]) -> list[Verdict]:
        return [self.judge(case) for case in cases]

    def judge(self, case: dict) -> Verdict:
        result = self.reader.read(case["question"], self.today)
        question = result.question
        got = {} if question is None else {"intent": question.intent, "metric": question.metric, "direction": question.direction, "month": question.month.strftime("%Y-%m")}
        outcome = "answer" if question else ("widgets" if result.problem in PLANNER_PROBLEMS else "refuse")
        expected = case["outcome"]
        if expected == "answer":
            passed = question is not None and all(got[key] == case[key] for key in ("intent", "metric", "month") + (("direction",) if case["intent"] == "why" else ()))
        elif expected == "widgets":
            passed = outcome == "widgets"
        else:
            passed = result.problem == case["problem"] or (case["problem"] == "unreadable" and result.problem in PLANNER_PROBLEMS)
        return Verdict(case, outcome, result.problem, got, passed, wrong_answer=question is not None and expected != "answer")


def summarise(verdicts: list[Verdict]) -> dict:
    answers = [v for v in verdicts if v.case["outcome"] == "answer"]
    others = [v for v in verdicts if v.case["outcome"] != "answer"]
    return {
        "cases": len(verdicts),
        "passed": sum(v.passed for v in verdicts),
        "answers_right": f"{sum(v.passed for v in answers)}/{len(answers)}",
        "refusals_right": f"{sum(v.passed for v in others)}/{len(others)}",
        "wrong_answers": sum(v.wrong_answer for v in verdicts),
    }
