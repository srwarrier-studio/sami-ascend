import json
from pathlib import Path

from intent_api.application.read_domain import OTHER
from intent_api.domain.entities.eval_case import EvalCase
from intent_api.domain.entities.scenario import Library
from intent_api.domain.errors import LibraryError

QUESTIONS_FILE = Path(__file__).resolve().parents[3] / "evals" / "questions.json"
PARTS = {"single", "multi", "refuse"}


def load_cases(library: Library, path: Path = QUESTIONS_FILE) -> list[EvalCase]:
    try:
        rows = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise LibraryError([f"questions {path.name}: {error}"]) from error
    problems = []
    cases = []
    seen = set()
    for index, row in enumerate(rows, start=1):
        label = f"question #{index}"
        found = len(problems)
        if not isinstance(row, dict):
            problems.append(f"{label}: must be an object")
            continue
        case_id = row.get("id")
        if not isinstance(case_id, str) or not case_id or case_id in seen:
            problems.append(f"{label}: needs a unique id")
        seen.add(case_id)
        if not isinstance(row.get("question"), str) or not row["question"].strip():
            problems.append(f"{label}: needs a question")
        if row.get("part") not in PARTS:
            problems.append(f"{label}: part must be one of {sorted(PARTS)}")
        if row.get("domain") not in {*library.domains, OTHER}:
            problems.append(f"{label}: unknown domain '{row.get('domain')}'")
        scenarios = row.get("scenarios")
        if not isinstance(scenarios, list) or any(item not in library.scenarios for item in scenarios):
            problems.append(f"{label}: scenarios must be a list of known scenario ids")
        elif (row.get("part") == "refuse") != (not scenarios):
            problems.append(f"{label}: only 'refuse' questions have no scenarios")
        if not isinstance(row.get("heldout"), bool):
            problems.append(f"{label}: heldout must be true or false")
        if len(problems) == found:
            cases.append(EvalCase(case_id, row["question"], row["part"], row["domain"], frozenset(scenarios), row["heldout"]))
    if problems:
        raise LibraryError(problems)
    return cases
