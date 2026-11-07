import tomllib
from pathlib import Path

from intent_api.domain.errors import LibraryError

QUALIFIER_WORDS_FILE = Path(__file__).resolve().parents[3] / "qualifier_words.toml"
GROUPS = {"company_markers", "quantity", "other_currencies", "countries", "own_names", "ignored_capitals"}


def load_qualifier_words(path: Path = QUALIFIER_WORDS_FILE) -> dict[str, list[str]]:
    try:
        words = tomllib.loads(path.read_text()).get("words", {})
    except (OSError, tomllib.TOMLDecodeError) as error:
        raise LibraryError([f"qualifier words {path.name}: {error}"]) from error
    problems = [f"qualifier words: unknown group '{name}'" for name in set(words) - GROUPS]
    problems += [f"qualifier words: missing group '{name}'" for name in GROUPS - set(words)]
    problems += [f"qualifier words: '{name}' must be a list of text" for name, items in words.items() if not isinstance(items, list) or not all(isinstance(item, str) and item for item in items)]
    if problems:
        raise LibraryError(problems)
    return {name: [item.lower() for item in items] for name, items in words.items()}
