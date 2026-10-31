import argparse
import json
from datetime import date
from pathlib import Path

from sami_agents.application.analyse_question import AnalyseQuestion
from sami_agents.application.answer_question import AnswerQuestion
from sami_agents.application.question_reader import QuestionReader
from sami_agents.application.score_answer import Score, score
from sami_agents.infrastructure.graph_loader import load_graph
from sami_agents.infrastructure.in_process_stack import stack_for
from sami_agents.infrastructure.settings import GRAPH_FILE
from sami_agents.infrastructure.understanding_loader import load_understanding

EVALS = Path(__file__).resolve().parents[3] / "evals"
SCENARIOS = Path(__file__).resolve().parents[4] / "butterfly" / "scenarios"
EVAL_TODAY = date(2026, 11, 2)
HINTS = {"cancelled_orders": "needs a sales_order record type in the registry, a graph node for it and a rate-change anomaly kind (not built)"}


def run_case(case: dict, graph=None) -> tuple[Score, dict]:
    truth = json.loads((SCENARIOS / f"{case['scenario']}.json").read_text())
    source, token = stack_for(case["scenario"], EVAL_TODAY)
    understanding = load_understanding()
    analyser = AnalyseQuestion(source, graph or load_graph(GRAPH_FILE))
    answer = AnswerQuestion(QuestionReader(understanding), analyser, source, list(understanding.metrics)).execute(case["question"], token, EVAL_TODAY)
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
    parser = argparse.ArgumentParser(prog="sami-agents analyst-eval")
    parser.add_argument("--final", action="store_true", help="also run the held-back scenarios")
    args = parser.parse_args(argv)
    cases = json.loads((EVALS / "analyst.json").read_text())
    if args.final:
        cases += json.loads((EVALS / "analyst_final.json").read_text())
    results = []
    for case in cases:
        result, _ = run_case(case)
        truth = json.loads((SCENARIOS / f"{case['scenario']}.json").read_text())
        results.append(result)
        print(describe(result, len(truth["causes"])), flush=True)
    passed = sum(r.passed for r in results)
    print(f"\n{passed}/{len(results)} scenarios passed")
    print(f"causes found {sum(len(r.found) for r in results)}, missed {sum(len(r.missed) for r in results)}, invented {sum(len(r.invented) for r in results)}, blamed wrongly {sum(len(r.blamed) for r in results)}")
