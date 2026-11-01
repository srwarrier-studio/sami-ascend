import tomllib
from pathlib import Path

from intent_api.domain.entities.scenario import SLOTS, Library, Scenario
from intent_api.domain.errors import LibraryError

SCENARIOS_FILE = Path(__file__).resolve().parents[3] / "scenarios.toml"
SCENARIO_KEYS = {"id", "domain", "description", "examples", "needs", "covers"}


def load_library(path: Path = SCENARIOS_FILE) -> Library:
    try:
        data = tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise LibraryError([f"library {path.name}: {error}"]) from error
    problems: list[str] = []
    for section in set(data) - {"domain", "scenario"}:
        problems.append(f"library: unknown section '{section}'")
    domains = read_domains(data.get("domain", {}), problems)
    scenarios = read_scenarios(data.get("scenario", []), domains, problems)
    check_covers(scenarios, problems)
    if problems:
        raise LibraryError(problems)
    return Library(domains, scenarios)


def load_domains(path: Path = SCENARIOS_FILE) -> dict[str, str]:
    return load_library(path).domains


def read_domains(section, problems: list[str]) -> dict[str, str]:
    if not isinstance(section, dict):
        problems.append("library: 'domain' must be a table of domains")
        return {}
    domains = {}
    for name, body in section.items():
        description = body.get("description", "") if isinstance(body, dict) else ""
        if not isinstance(description, str) or not description.strip():
            problems.append(f"domain '{name}': needs a description")
        else:
            domains[name] = description.strip()
    if not domains and not problems:
        problems.append("library: no domains")
    return domains


def read_scenarios(entries, domains: dict[str, str], problems: list[str]) -> dict[str, Scenario]:
    if not isinstance(entries, list):
        problems.append("library: 'scenario' must be a list of [[scenario]] tables")
        return {}
    scenarios: dict[str, Scenario] = {}
    for index, body in enumerate(entries, start=1):
        scenario = read_scenario(index, body, domains, problems)
        if scenario is None:
            continue
        if scenario.id in scenarios:
            problems.append(f"scenario '{scenario.id}': duplicate id")
        scenarios[scenario.id] = scenario
    return scenarios


def read_scenario(index: int, body, domains: dict[str, str], problems: list[str]) -> Scenario | None:
    if not isinstance(body, dict):
        problems.append(f"scenario #{index}: must be a table")
        return None
    name = body.get("id")
    has_id = isinstance(name, str) and bool(name.strip())
    label = f"scenario '{name}'" if has_id else f"scenario #{index}"
    found = len(problems)
    for key in set(body) - SCENARIO_KEYS:
        problems.append(f"{label}: unknown key '{key}'")
    if not has_id:
        problems.append(f"{label}: needs an id")
    if body.get("domain") not in domains:
        problems.append(f"{label}: unknown domain '{body.get('domain')}'")
    description = body.get("description", "")
    if not isinstance(description, str) or not description.strip():
        problems.append(f"{label}: needs a description")
    examples = text_list(body.get("examples", []))
    if not examples:
        problems.append(f"{label}: needs at least one example")
    needs = text_list(body.get("needs", []))
    covers = text_list(body.get("covers", []))
    if needs is None or covers is None:
        problems.append(f"{label}: 'needs' and 'covers' must be lists of text")
        return None
    for slot in needs:
        if slot not in SLOTS:
            problems.append(f"{label}: unknown slot '{slot}' (known: {', '.join(SLOTS)})")
    if len(problems) > found:
        return None
    return Scenario(name.strip(), body["domain"], description.strip(), tuple(examples), tuple(needs), tuple(covers))


def text_list(value) -> list[str] | None:
    if not isinstance(value, list) or not all(isinstance(item, str) and item.strip() for item in value):
        return None
    return value


def check_covers(scenarios: dict[str, Scenario], problems: list[str]) -> None:
    for scenario in scenarios.values():
        for other in scenario.covers:
            if other not in scenarios:
                problems.append(f"scenario '{scenario.id}': covers unknown scenario '{other}'")
    for scenario in scenarios.values():
        if loops(scenario.id, scenarios):
            problems.append(f"scenario '{scenario.id}': covers loops back to itself")


def loops(start: str, scenarios: dict[str, Scenario]) -> bool:
    seen: set[str] = set()
    pending = list(scenarios[start].covers)
    while pending:
        current = pending.pop()
        if current == start:
            return True
        if current in seen or current not in scenarios:
            continue
        seen.add(current)
        pending.extend(scenarios[current].covers)
    return False
