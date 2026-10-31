import json
from dataclasses import dataclass
from pathlib import Path

UNDERSTANDING_FILE = Path(__file__).resolve().parents[3] / "understanding.json"


@dataclass(frozen=True)
class Understanding:
    metrics: dict[str, list[str]]
    why: list[str]
    figure: list[str]
    rise: list[str]
    fall: list[str]
    change: list[str]


def load_understanding(path: Path = UNDERSTANDING_FILE) -> Understanding:
    data = json.loads(path.read_text(encoding="utf-8"))
    words = lambda value: isinstance(value, list) and all(isinstance(w, str) and w for w in value)
    ok = isinstance(data, dict) and isinstance(data.get("metrics"), dict) and all(words(v) and v for v in data["metrics"].values())
    ok = ok and all(words(data.get(name)) and data.get(name) for name in ("why", "figure", "rise", "fall", "change"))
    if not ok:
        raise ValueError(f"{path.name} must hold word lists for metrics, why, figure, rise, fall and change")
    return Understanding(data["metrics"], data["why"], data["figure"], data["rise"], data["fall"], data["change"])
