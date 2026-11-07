import tomllib
from pathlib import Path

from intent_api.domain.errors import LibraryError

PERIOD_WORDS_FILE = Path(__file__).resolve().parents[3] / "period_words.toml"
GROUPS = {"last", "this", "range_to", "between", "and", "financial_year", "year_to_date", "month_to_date", "unreadable", "metric_phrases"}


def load_period_words(path: Path = PERIOD_WORDS_FILE) -> dict[str, list[str]]:
    try:
        words = tomllib.loads(path.read_text()).get("words", {})
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise LibraryError([f"period words {path.name}: {error}"]) from error
    problems = [f"period words: unknown group '{name}'" for name in set(words) - GROUPS]
    problems += [f"period words: missing group '{name}'" for name in GROUPS - set(words)]
    problems += [f"period words: '{name}' must be a list of text" for name, items in words.items() if not isinstance(items, list) or not all(isinstance(item, str) and item for item in items)]
    if problems:
        raise LibraryError(problems)
    return {name: [item.lower() for item in items] for name, items in words.items()}
