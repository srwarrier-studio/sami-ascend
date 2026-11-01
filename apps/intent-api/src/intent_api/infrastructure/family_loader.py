import re
import tomllib
from pathlib import Path

from intent_api.application.read_domain import OTHER
from intent_api.domain.entities.scenario import Library
from intent_api.domain.entities.training import Family
from intent_api.domain.errors import LibraryError

FAMILIES_FILE = Path(__file__).resolve().parents[5] / "Training" / "families.toml"
SLOT = re.compile(r"\{(\w+)\}")
HELDOUT_EVERY = 4


def load_families(library: Library, path: Path = FAMILIES_FILE) -> tuple[list[Family], dict[str, list[str]]]:
    try:
        data = tomllib.loads(path.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise LibraryError([f"families {path.name}: {error}"]) from error
    problems: list[str] = []
    slots = read_slots(data.get("slots", {}), problems)
    rows = data.get("family", [])
    families = [family for index, row in enumerate(rows, start=1) if (family := read_family(index, row, library, slots, problems))]
    for family_id in {family.id for family in families if [f.id for f in families].count(family.id) > 1}:
        problems.append(f"family '{family_id}': duplicate id")
    if problems:
        raise LibraryError(problems)
    return mark_heldout(families), slots


def read_slots(section, problems: list[str]) -> dict[str, list[str]]:
    if not isinstance(section, dict) or not section:
        problems.append("families: needs a [slots] table")
        return {}
    slots = {}
    for name, values in section.items():
        if not isinstance(values, list) or not values or not all(isinstance(value, str) and value.strip() for value in values):
            problems.append(f"slot '{name}': needs a list of text values")
        else:
            slots[name] = values
    return slots


def read_family(index: int, row, library: Library, slots: dict[str, list[str]], problems: list[str]) -> Family | None:
    if not isinstance(row, dict):
        problems.append(f"family #{index}: must be a table")
        return None
    name = row.get("id")
    label = f"family '{name}'" if isinstance(name, str) and name else f"family #{index}"
    found = len(problems)
    if label.startswith("family #"):
        problems.append(f"{label}: needs an id")
    domain, scenario, nothing = row.get("domain"), row.get("scenario"), row.get("nothing", False)
    if domain not in {*library.domains, OTHER}:
        problems.append(f"{label}: unknown domain '{domain}'")
    if scenario is not None and (scenario not in library.scenarios or library.scenarios[scenario].domain != domain):
        problems.append(f"{label}: scenario '{scenario}' is not a scenario of domain '{domain}'")
    if scenario is not None and nothing:
        problems.append(f"{label}: a family with a scenario cannot also be 'nothing'")
    if nothing is not True and nothing is not False:
        problems.append(f"{label}: 'nothing' must be true or false")
    templates = row.get("templates")
    if not isinstance(templates, list) or not templates or not all(isinstance(text, str) and text.strip() for text in templates):
        problems.append(f"{label}: needs a list of templates")
    else:
        for text in templates:
            for slot in SLOT.findall(text):
                if slot not in slots:
                    problems.append(f"{label}: template '{text}' uses unknown slot '{slot}'")
    if len(problems) > found:
        return None
    return Family(name, domain, scenario, nothing, tuple(templates), False)


def mark_heldout(families: list[Family]) -> list[Family]:
    groups: dict[tuple, list[Family]] = {}
    for family in sorted(families, key=lambda item: item.id):
        groups.setdefault((family.domain, family.scenario, family.nothing), []).append(family)
    held = {family.id for members in groups.values() for position, family in enumerate(members, start=1) if position % HELDOUT_EVERY == 0}
    return [Family(f.id, f.domain, f.scenario, f.nothing, f.templates, f.id in held) for f in families]
