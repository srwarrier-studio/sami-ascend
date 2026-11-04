import argparse
import json
from datetime import date
from pathlib import Path

from intent_api.application.analysis import why_wording
from intent_api.application.analysis.analyse_question import AnalyseQuestion
from intent_api.application.analysis.analysis_json import analysis_json
from intent_api.application.analysis.score_answer import Score, score
from intent_api.application.read_direction import read_direction
from intent_api.application.read_period import ReadPeriod
from intent_api.domain.analysis.question import Question
from intent_api.infrastructure.graph_loader import load_graph
from intent_api.infrastructure.in_process_stack import stack_for
from intent_api.infrastructure.settings import GRAPH_FILE

EVALS = Path(__file__).resolve().parents[3] / "evals"
SCENARIOS = Path(__file__).resolve().parents[4] / "butterfly" / "scenarios"
EVAL_TODAY = date(2026, 11, 2)
STORY_COMPANY = "sabinsa"
CURRENCIES = {"sales": "INR", "purchases": "INR"}
HINTS = {"cancelled_orders": "needs a sales_order record type in the registry, a graph node for it and a rate-change anomaly kind (not built)"}


def run_case(case: dict, graph=None, company: str = STORY_COMPANY, currency: str | None = "default") -> tuple[Score, dict]:
    truth = json.loads((SCENARIOS / f"{case['scenario']}.json").read_text())
    source, token = stack_for(case["scenario"], EVAL_TODAY)
    month = ReadPeriod().execute(case["question"], EVAL_TODAY).start
    question = Question(truth["metric"], read_direction(case["question"]), month, currency=CURRENCIES[truth["metric"]] if currency == "default" else currency)
    scoped = source.for_company(None if company == "all" else company)
    analysis = AnalyseQuestion(scoped, graph or load_graph(GRAPH_FILE)).execute(question, token, EVAL_TODAY)
    answer = {"analysis": analysis_json(analysis), "lines": why_wording.lines(analysis, company)}
    return score(case["scenario"], truth, answer), answer


def describe(result: Score, truth_causes: int) -> str:
    mark = "PASS" if result.passed else "FAIL"
    lines = [f"[{mark}] {result.scenario}: found {len(result.found)} of {truth_causes} causes, missed {len(result.missed)}, invented {len(result.invented)}, blamed {len(result.blamed)}"]
    for label, items in (("found", result.found), ("missed", result.missed), ("invented", result.invented), ("blamed wrongly", result.blamed)):
        lines += [f"         {label}: {item}" + (f"  -> {HINTS[item.split()[0]]}" if label == "missed" and item.split()[0] in HINTS else "") for item in items]
    for ok, text in ((result.change_ok, "the change is outside the expected range"), (result.unexplained_ok, "the unexplained rest does not match the truth"), (result.quiet_ok, "a quiet month got findings")):
        if not ok:
            lines.append(f"         {text}")
    return "\n".join(lines)


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="intent-api why-eval")
    parser.add_argument("--final", action="store_true", help="also run the held-back scenarios")
    args = parser.parse_args(argv)
    cases = json.loads((EVALS / "why.json").read_text())
    if args.final:
        cases += json.loads((EVALS / "why_final.json").read_text())
    results = []
    for case in cases:
        result, _ = run_case(case)
        truth = json.loads((SCENARIOS / f"{case['scenario']}.json").read_text())
        results.append(result)
        print(describe(result, len(truth["causes"])), flush=True)
    passed = sum(r.passed for r in results)
    print(f"\n{passed}/{len(results)} scenarios passed")
    print(f"causes found {sum(len(r.found) for r in results)}, missed {sum(len(r.missed) for r in results)}, invented {sum(len(r.invented) for r in results)}, blamed wrongly {sum(len(r.blamed) for r in results)}")
