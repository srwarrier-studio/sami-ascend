import argparse
import json
import time
from pathlib import Path

from sami_agents.application.evaluate_agent import CaseResult, EvalCase, EvaluateAgent
from sami_agents.application.keyword_matcher import KeywordMatcher
from sami_agents.application.plan_chat import DEFAULT_THRESHOLD
from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.infrastructure.alias_book import ALIASES_FILE, load_aliases

EVALS = Path(__file__).resolve().parents[3] / "evals"


def load_catalog(path: Path) -> list[CatalogEntry]:
    return [CatalogEntry(row["id"], row["title"], row["description"]) for row in json.loads(path.read_text())]


def load_cases(path: Path) -> list[EvalCase]:
    return [EvalCase(row["message"], row["expected"], row.get("minimum", 1)) for row in json.loads(path.read_text())]


def describe(result: CaseResult) -> str:
    mark = "pass" if result.final_pass else "FAIL"
    checked = "unchecked" if result.unchecked else f"{result.checks} checks"
    return (
        f"[{mark}] {result.seconds:5.1f}s {checked:<10} {result.case.message}\n"
        f"         got {result.final} expected {result.case.expected} rejected {result.rejected}"
    )


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="sami-agents eval")
    parser.add_argument("--parallel", type=int, default=1, help="run the prompts as this many batches at the same time")
    parser.add_argument("--aliases", default=str(ALIASES_FILE), help="alias file, or none")
    parser.add_argument("--threshold", type=float, default=DEFAULT_THRESHOLD, help="smallest relevance score that approves a widget")
    parser.add_argument("--prompts", type=Path, default=EVALS / "prompts.json")
    parser.add_argument("--catalog", type=Path, default=EVALS / "catalog.json")
    args = parser.parse_args(argv)
    aliases = {} if args.aliases == "none" else load_aliases(Path(args.aliases))
    agent = EvaluateAgent(None, load_catalog(args.catalog), KeywordMatcher(aliases), args.threshold)
    started = time.perf_counter()
    results = agent.execute(load_cases(args.prompts), args.parallel, lambda result: print(describe(result), flush=True))
    wall = time.perf_counter() - started
    summary = EvaluateAgent.summarise(results)
    print(f"\n{summary.cases} prompts, {args.parallel} at a time")
    print(f"keywords alone passed:    {summary.proposed_pass}/{summary.cases}")
    print(f"whole pipeline passed:    {summary.final_pass}/{summary.cases}")
    print(f"answered without a check: {summary.unchecked}/{summary.cases}")
    print(f"checks per answer:        {summary.average_checks:.1f}")
    print(f"seconds per answer:       {summary.average_seconds:.1f} average, {summary.slowest_seconds:.1f} slowest")
    print(f"total time:               {wall:.1f}s")
