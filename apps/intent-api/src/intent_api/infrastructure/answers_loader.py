import tomllib
from pathlib import Path

from intent_api.domain.entities.answer import AGAINST, RESPONSES, AnswerRule
from intent_api.domain.entities.scenario import Library
from intent_api.domain.errors import LibraryError

ANSWERS_FILE = Path(__file__).resolve().parents[3] / "answers.toml"
ANSWER_KEYS = {"scenario", "response", "metric", "by", "against"}


def load_answers(library: Library, path: Path = ANSWERS_FILE) -> dict[str, AnswerRule]:
    try:
        data = tomllib.loads(path.read_text())
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise LibraryError([f"answers {path.name}: {error}"]) from error
    problems: list[str] = []
    for section in set(data) - {"answer"}:
        problems.append(f"answers: unknown section '{section}'")
    entries = data.get("answer", [])
    if not isinstance(entries, list):
        raise LibraryError(["answers: 'answer' must be a list of [[answer]] tables"])
    rules: dict[str, AnswerRule] = {}
    for index, body in enumerate(entries, start=1):
        rule = read_rule(index, body, library, problems)
        if rule is None:
            continue
        if rule.scenario in rules:
            problems.append(f"answer '{rule.scenario}': duplicate scenario")
        rules[rule.scenario] = rule
    if problems:
        raise LibraryError(problems)
    return rules


def read_rule(index: int, body, library: Library, problems: list[str]) -> AnswerRule | None:
    if not isinstance(body, dict):
        problems.append(f"answer #{index}: must be a table")
        return None
    scenario = body.get("scenario")
    label = f"answer '{scenario}'" if isinstance(scenario, str) else f"answer #{index}"
    found = len(problems)
    for key in set(body) - ANSWER_KEYS:
        problems.append(f"{label}: unknown key '{key}'")
    if scenario not in library.scenarios:
        problems.append(f"{label}: unknown scenario '{scenario}'")
    response = body.get("response")
    if response not in RESPONSES:
        problems.append(f"{label}: unknown response '{response}' (known: {', '.join(RESPONSES)})")
    metric = body.get("metric")
    if not isinstance(metric, str) or not metric.strip():
        problems.append(f"{label}: needs a metric")
    by, against = body.get("by"), body.get("against")
    if response == "ranking" and not (isinstance(by, str) and by.strip()):
        problems.append(f"{label}: a ranking needs 'by'")
    if response != "ranking" and by is not None:
        problems.append(f"{label}: only a ranking has 'by'")
    if response == "compare" and against not in AGAINST:
        problems.append(f"{label}: a compare needs 'against' ({', '.join(AGAINST)})")
    if response != "compare" and against is not None:
        problems.append(f"{label}: only a compare has 'against'")
    if len(problems) > found:
        return None
    return AnswerRule(scenario, response, metric.strip(), by, against)
