import re

from sami_agents.domain.entities.catalog import CatalogEntry

STOP_WORDS = {
    "the", "and", "for", "with", "show", "give", "get", "can", "you", "please", "me", "my", "our",
    "what", "how", "are", "was", "were", "is", "of", "in", "on", "to", "a", "an", "all", "this", "that",
    "builder", "build", "make", "create", "board", "dashboard", "view", "see", "want", "need", "about",
}
MIN_WORD = 3


def words(text: str) -> set[str]:
    return {word for word in re.findall(r"[a-z0-9]+", text.lower()) if len(word) >= MIN_WORD and word not in STOP_WORDS}


class KeywordMatcher:
    def match(self, message: str, catalog: list[CatalogEntry], limit: int) -> list[str]:
        asked = words(message)
        scored = [(len(asked & words(f"{entry.title} {entry.description}")), index, entry.id) for index, entry in enumerate(catalog)]
        ranked = sorted((item for item in scored if item[0] > 0), key=lambda item: (-item[0], item[1]))
        return [entry_id for _, _, entry_id in ranked[:limit]]
