import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import httpx

HELDOUT = Path(__file__).resolve().parents[3] / "Training" / "out" / "heldout.jsonl"
LEVELS = [1, 5, 10, 20]
REQUESTS_PER_LEVEL = 120


def run_level(url: str, bodies: list[dict], parallel: int) -> dict:
    latencies = []

    def call(body: dict) -> None:
        started = time.perf_counter()
        response = client.post("/v1/systemone", json=body)
        response.raise_for_status()
        latencies.append(time.perf_counter() - started)

    started = time.perf_counter()
    with httpx.Client(base_url=url, timeout=120, limits=httpx.Limits(max_connections=parallel)) as client, ThreadPoolExecutor(parallel) as pool:
        list(pool.map(call, bodies))
    elapsed = time.perf_counter() - started
    latencies.sort()
    return {
        "parallel": parallel,
        "calls_per_second": round(len(bodies) / elapsed, 2),
        "p50_ms": round(latencies[len(latencies) // 2] * 1000),
        "p95_ms": round(latencies[int(len(latencies) * 0.95)] * 1000),
        "max_ms": round(latencies[-1] * 1000),
    }


def main(url: str) -> None:
    items = [json.loads(line) for line in HELDOUT.read_text().splitlines() if line.strip()]
    bodies = [{"state": item["state"], "questions": item["questions"]} for item in items[:REQUESTS_PER_LEVEL]]
    for parallel in LEVELS:
        print(json.dumps(run_level(url, bodies, parallel)), flush=True)
        print(f"level {parallel} done", file=sys.stderr, flush=True)


if __name__ == "__main__":
    main(sys.argv[1])
