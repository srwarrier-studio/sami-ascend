import re

from sami_agents.domain.entities.catalog import CatalogEntry

STOP_WORDS = {
    "the", "and", "for", "with", "show", "give", "get", "can", "you", "please", "me", "my", "our",
    "what", "how", "are", "was", "were", "is", "of", "in", "on", "to", "a", "an", "all", "this", "that",
    "builder", "build", "make", "create", "board", "dashboard", "view", "see", "want", "need", "about",
    "much", "many", "who", "which", "does", "did", "have", "has", "from", "far", "now", "tell",
}
MIN_WORD = 3
SUFFIXES = ("ing", "ed", "es", "s")
STRONG = 2
WEAK = 1


def stem(word: str) -> str:
    stemmed = word
    for suffix in SUFFIXES:
        if word.endswith(suffix) and len(word) - len(suffix) >= MIN_WORD:
            stemmed = word[: -len(suffix)]
            break
    if stemmed.endswith("e") and len(stemmed) - 1 >= MIN_WORD:
        stemmed = stemmed[:-1]
    if len(stemmed) > MIN_WORD and stemmed[-1] == stemmed[-2] and stemmed[-1] not in "aeiouls":
        stemmed = stemmed[:-1]
    return stemmed


def words(text: str) -> set[str]:
    return {stem(word) for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) >= MIN_WORD and word not in STOP_WORDS}


class KeywordMatcher:
    def __init__(self, aliases: dict[str, list[str]] | None = None):
        self.aliases = aliases or {}

    def rank(self, message: str, catalog: list[CatalogEntry], skip: set[str] | frozenset[str] = frozenset()) -> list[str]:
        asked = words(message)
        scored = []
        for index, entry in enumerate(catalog):
            if entry.id in skip:
                continue
            strong = words(entry.title) | words(" ".join(self.aliases.get(entry.id, [])))
            weak = words(entry.description) - strong
            score = STRONG * len(asked & strong) + WEAK * len(asked & weak)
            if score > 0:
                scored.append((-score, index, entry.id))
        return [entry_id for _, _, entry_id in sorted(scored)]

    def match(self, message: str, catalog: list[CatalogEntry], limit: int) -> list[str]:
        return self.rank(message, catalog)[:limit]
