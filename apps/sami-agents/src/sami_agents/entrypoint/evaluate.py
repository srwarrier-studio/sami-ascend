import argparse
import json
import time
from pathlib import Path

from sami_agents.application.evaluate_agent import CaseResult, EvalCase, EvaluateAgent
from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.infrastructure.ollama_chat_model import OllamaChatModel
from sami_agents.infrastructure.settings import Settings

EVALS = Path(__file__).resolve().parents[3] / "evals"


def load_catalog(path: Path) -> list[CatalogEntry]:
    return [CatalogEntry(row["id"], row["title"], row["description"]) for row in json.loads(path.read_text())]


def load_cases(path: Path) -> list[EvalCase]:
    return [EvalCase(row["message"], row["expected"], row.get("minimum", 1)) for row in json.loads(path.read_text())]


def describe(result: CaseResult) -> str:
    mark = "pass" if result.final_pass else "FAIL"
    model = "model ok" if result.model_pass else f"model {result.status}" if result.status != "ok" else "model missed"
    return f"[{mark}] {result.seconds:5.1f}s {model:<18} {result.case.message}\n         got {result.final} expected {result.case.expected}"


def main(argv: list[str]) -> None:
    parser = argparse.ArgumentParser(prog="sami-agents eval")
    parser.add_argument("--model", help="Ollama model name (default OLLAMA_MODEL)")
    parser.add_argument("--parallel", type=int, default=1, help="run the prompts as this many batches at the same time")
    parser.add_argument("--prompts", type=Path, default=EVALS / "prompts.json")
    parser.add_argument("--catalog", type=Path, default=EVALS / "catalog.json")
    args = parser.parse_args(argv)
    settings = Settings()
    if args.model:
        settings = settings.model_copy(update={"ollama_model": args.model})
    agent = EvaluateAgent(OllamaChatModel(settings), load_catalog(args.catalog))
    started = time.perf_counter()
    results = agent.execute(load_cases(args.prompts), args.parallel, lambda result: print(describe(result), flush=True))
    wall = time.perf_counter() - started
    summary = EvaluateAgent.summarise(results)
    print(f"\nmodel {settings.ollama_model}, {summary.cases} prompts, {args.parallel} at a time")
    print(f"model answered validly:   {summary.answered}/{summary.cases}")
    print(f"model alone passed:       {summary.model_pass}/{summary.cases}")
    print(f"with keyword fallback:    {summary.final_pass}/{summary.cases}")
    print(f"fallback was needed:      {summary.fallback}/{summary.cases}")
    print(f"seconds per answer:       {summary.average_seconds:.1f} average, {summary.slowest_seconds:.1f} slowest")
    print(f"total time:               {wall:.1f}s")
