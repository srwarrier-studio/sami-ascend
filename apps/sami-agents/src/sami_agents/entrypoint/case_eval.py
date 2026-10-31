import argparse
import json
from datetime import date
from pathlib import Path

from sami_agents.application.case_reader import CaseReader
from sami_agents.application.evaluate_cases import EvaluateCases, Verdict, summarise
from sami_agents.application.question_reader import QuestionReader
from sami_agents.infrastructure.laya_case_model import LayaCaseModel
from sami_agents.infrastructure.settings import Settings
from sami_agents.infrastructure.understanding_loader import load_understanding

EVALS = Path(__file__).resolve().parents[3] / "evals"
EVAL_TODAY = date(2026, 10, 31)


def describe(verdict: Verdict) -> str:
    case = verdict.case
    expected = {key: case[key] for key in ("intent", "metric", "direction", "month") if key in case} or case.get("problem") or case["outcome"]
    return f"[FAIL] {case['question']!r}\n         expected {expected} got {verdict.got or verdict.problem}"


def report(name: str, verdicts: list[Verdict]) -> None:
    print(f"-- {name}")
    for verdict in verdicts:
        if not verdict.passed:
            print(describe(verdict))
    print(" ".join(f"{key}={value}" for key, value in summarise(verdicts).items()))


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="sami-agents case-eval")
    parser.add_argument("--final", action="store_true", help="also run the held-out questions")
    args = parser.parse_args(argv)
    settings = Settings()
    rules = QuestionReader(load_understanding())
    readers = {"rules only": rules}
    if settings.laya_url:
        readers["Laya on"] = CaseReader(rules, LayaCaseModel(settings), settings.pass_min_confidence)
    else:
        print("LAYA_URL is not set: only the rules are measured")
    sets = {"tuning set": "cases.json"} | ({"held-out set": "cases_heldout.json"} if args.final else {})
    for set_name, file in sets.items():
        cases = json.loads((EVALS / file).read_text())
        for reader_name, reader in readers.items():
            report(f"{set_name}, {reader_name}", EvaluateCases(reader, EVAL_TODAY).run(cases))
