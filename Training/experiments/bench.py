import json
import resource
import sys
import time
from collections.abc import Callable
from pathlib import Path

import httpx

Scorer = Callable[[str, str, dict[str, str]], dict[str, float]]

HELDOUT = Path(__file__).resolve().parent.parent / "heldout.jsonl"


def http_scorer(url: str, api_key: str = "", model: str = "typed-decisions") -> Scorer:
    client = httpx.Client(base_url=url, timeout=60, headers={"Authorization": f"Bearer {api_key}"} if api_key else {})

    def score(text: str, instructions: str, choices: dict[str, str]) -> dict[str, float]:
        body = {
            "state": {"question": text},
            "questions": {"choice": {"type": "choice", "instructions": instructions, "criteria": choices}},
            "model": model,
        }
        response = client.post("/v1/systemone", json=body)
        response.raise_for_status()
        return response.json()["answers"]["choice"]["probabilities"]

    return score


def expected_calibration_error(results: list[tuple[float, bool]], bins: int = 10) -> float:
    total = len(results)
    error = 0.0
    for index in range(bins):
        low, high = index / bins, (index + 1) / bins
        bucket = [(c, ok) for c, ok in results if low < c <= high or (index == 0 and c == 0)]
        if bucket:
            confidence = sum(c for c, _ in bucket) / len(bucket)
            accuracy = sum(ok for _, ok in bucket) / len(bucket)
            error += len(bucket) / total * abs(confidence - accuracy)
    return error


def evaluate(scorer: Scorer, path: Path = HELDOUT, limit: int | None = None) -> dict[str, float]:
    items = [json.loads(line) for line in path.read_text().splitlines() if line.strip()]
    items = items[:limit] if limit else items
    results, latencies = [], []
    started_all = time.perf_counter()
    for done, item in enumerate(items, start=1):
        question = item["questions"]["choice"]
        started = time.perf_counter()
        probabilities = scorer(item["state"]["question"], question["instructions"], question["criteria"])
        latencies.append(time.perf_counter() - started)
        best = max(probabilities, key=probabilities.get)
        results.append((probabilities[best], best == item["expected"]["choice"]))
        if done % 50 == 0 or done == len(items):
            elapsed = time.perf_counter() - started_all
            print(f"{done}/{len(items)} elapsed {elapsed:.0f}s eta {elapsed / done * (len(items) - done):.0f}s", file=sys.stderr, flush=True)
    latencies.sort()
    return {
        "items": len(items),
        "accuracy": round(sum(ok for _, ok in results) / len(items), 4),
        "ece": round(expected_calibration_error(results), 4),
        "p50_ms": round(latencies[len(latencies) // 2] * 1000, 1),
        "p95_ms": round(latencies[int(len(latencies) * 0.95)] * 1000, 1),
        "peak_ram_mb": round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024),
    }


def first_choice(text: str, instructions: str, choices: dict[str, str]) -> dict[str, float]:
    return {name: 1.0 if index == 0 else 0.0 for index, name in enumerate(choices)}


if __name__ == "__main__":
    scorer = http_scorer(sys.argv[1], model=sys.argv[2] if len(sys.argv) > 2 else "typed-decisions") if len(sys.argv) > 1 else first_choice
    print(json.dumps(evaluate(scorer), indent=2))
