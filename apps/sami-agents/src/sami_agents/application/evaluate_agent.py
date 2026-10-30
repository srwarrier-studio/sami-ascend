import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from sami_agents.application.keyword_matcher import KeywordMatcher
from sami_agents.application.plan_chat import BOARD_LIMIT, BUILDER_TAG, DEFAULT_THRESHOLD, INLINE_LIMIT, PlanChat
from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.domain.gateways.relevance_checker import RelevanceChecker


@dataclass(frozen=True)
class EvalCase:
    message: str
    expected: list[str]
    minimum: int = 1


@dataclass(frozen=True)
class CaseResult:
    case: EvalCase
    proposed: list[str]
    final: list[str]
    rejected: list[str]
    checks: int
    unchecked: bool
    seconds: float
    proposed_pass: bool
    final_pass: bool


@dataclass(frozen=True)
class Summary:
    cases: int
    proposed_pass: int
    final_pass: int
    unchecked: int
    average_checks: float
    average_seconds: float
    slowest_seconds: float


def passes(case: EvalCase, ids: list[str]) -> bool:
    if not case.expected:
        return ids == []
    return len(set(ids) & set(case.expected)) >= case.minimum


class EvaluateAgent:
    def __init__(self, checker: RelevanceChecker | None, catalog: list[CatalogEntry], matcher: KeywordMatcher | None = None, threshold: float = DEFAULT_THRESHOLD):
        self.checker = checker
        self.catalog = catalog
        self.matcher = matcher or KeywordMatcher()
        self.threshold = threshold

    def execute(self, cases: list[EvalCase], parallel: int = 1, on_result: Callable[[CaseResult], None] | None = None) -> list[CaseResult]:
        size = -(-len(cases) // max(parallel, 1))
        batches = [list(enumerate(cases))[start : start + size] for start in range(0, len(cases), size)] if cases else []
        results: dict[int, CaseResult] = {}

        def run_batch(batch: list[tuple[int, EvalCase]]) -> None:
            for index, case in batch:
                results[index] = self.run(case)
                if on_result:
                    on_result(results[index])

        with ThreadPoolExecutor(max_workers=max(len(batches), 1)) as pool:
            list(pool.map(run_batch, batches))
        return [results[index] for index in range(len(cases))]

    def run(self, case: EvalCase) -> CaseResult:
        builder = case.message.strip().lower().startswith(BUILDER_TAG)
        request = case.message.strip()[len(BUILDER_TAG):].strip() if builder else case.message
        proposed = self.matcher.rank(request, self.catalog)[: BOARD_LIMIT if builder else INLINE_LIMIT]
        started = time.perf_counter()
        state = PlanChat(self.checker, self.matcher, self.threshold).run(case.message, self.catalog)
        seconds = time.perf_counter() - started
        return CaseResult(case, proposed, state["ids"], state["rejected"], state["checks"], state["unchecked"], seconds, passes(case, proposed), passes(case, state["ids"]))

    @staticmethod
    def summarise(results: list[CaseResult]) -> Summary:
        count = len(results) or 1
        seconds = [result.seconds for result in results]
        return Summary(
            cases=len(results),
            proposed_pass=sum(result.proposed_pass for result in results),
            final_pass=sum(result.final_pass for result in results),
            unchecked=sum(result.unchecked for result in results),
            average_checks=sum(result.checks for result in results) / count,
            average_seconds=sum(seconds) / count,
            slowest_seconds=max(seconds, default=0.0),
        )
