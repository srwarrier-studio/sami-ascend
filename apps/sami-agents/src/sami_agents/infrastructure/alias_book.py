import json
from pathlib import Path

ALIASES_FILE = Path(__file__).resolve().parents[3] / "aliases.json"


def load_aliases(path: Path = ALIASES_FILE) -> dict[str, list[str]]:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not all(isinstance(words, list) and all(isinstance(word, str) for word in words) for words in data.values()):
        raise ValueError(f"{path.name} must map each widget id to a list of words")
    return data
