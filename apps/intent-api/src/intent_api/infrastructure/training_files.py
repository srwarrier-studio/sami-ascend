import json
from pathlib import Path

from intent_api.application.choose_scenarios import NOTHING, NOTHING_DESCRIPTION
from intent_api.application.choose_scenarios import QUESTION as SCENARIO_QUESTION
from intent_api.application.read_domain import OTHER, OTHER_DESCRIPTION
from intent_api.application.read_domain import QUESTION as DOMAIN_QUESTION
from intent_api.domain.entities.scenario import Library
from intent_api.domain.entities.training import TrainingItem

QUESTION_ID = "choice"


def to_row(item: TrainingItem, library: Library) -> dict:
    if item.kind == "domain":
        descriptions = {**library.domains, OTHER: OTHER_DESCRIPTION}
        instructions = DOMAIN_QUESTION
    else:
        descriptions = {**{name: scenario.description for name, scenario in library.scenarios.items()}, NOTHING: NOTHING_DESCRIPTION}
        instructions = SCENARIO_QUESTION
    criteria = {name: descriptions[name] for name in item.offered}
    return {
        "state": {"question": item.text},
        "questions": {QUESTION_ID: {"type": "choice", "instructions": instructions, "criteria": criteria}},
        "expected": {QUESTION_ID: item.answer},
    }


def write_files(items: list[TrainingItem], library: Library, folder: Path) -> dict:
    folder.mkdir(parents=True, exist_ok=True)
    counts = {}
    for name, held in (("train", False), ("heldout", True)):
        chosen = [item for item in items if item.heldout == held]
        lines = [json.dumps(to_row(item, library), ensure_ascii=False) for item in chosen]
        (folder / f"{name}.jsonl").write_text("\n".join(lines) + "\n", encoding="utf-8")
        counts[name] = len(chosen)
    return counts
