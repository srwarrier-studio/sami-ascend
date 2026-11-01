import tomllib
from pathlib import Path

from intent_api.domain.errors import LibraryError

SCENARIOS_FILE = Path(__file__).resolve().parents[3] / "scenarios.toml"


def load_domains(path: Path = SCENARIOS_FILE) -> dict[str, str]:
    try:
        data = tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise LibraryError([f"library {path.name}: {error}"]) from error
    problems = []
    domains = {}
    section = data.get("domain", {})
    if not isinstance(section, dict):
        raise LibraryError(["library: 'domain' must be a table of domains"])
    for name, body in section.items():
        description = body.get("description", "") if isinstance(body, dict) else ""
        if not isinstance(description, str) or not description.strip():
            problems.append(f"domain '{name}': needs a description")
        else:
            domains[name] = description.strip()
    if not domains and not problems:
        problems.append("library: no domains")
    if problems:
        raise LibraryError(problems)
    return domains
