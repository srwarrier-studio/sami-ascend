from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.domain.errors import RelevanceUnavailable
from sami_agents.domain.gateways.relevance_checker import RelevanceChecker


class MockRelevanceChecker(RelevanceChecker):
    def __init__(self, scores: dict[str, float] | None = None, default: float = 1.0, fail_from: int | None = None):
        self.scores = scores or {}
        self.default = default
        self.fail_from = fail_from
        self.calls: list[tuple[str, str]] = []

    def check(self, message: str, entry: CatalogEntry) -> float:
        if self.fail_from is not None and len(self.calls) >= self.fail_from:
            raise RelevanceUnavailable()
        self.calls.append((message, entry.id))
        return self.scores.get(entry.id, self.default)
