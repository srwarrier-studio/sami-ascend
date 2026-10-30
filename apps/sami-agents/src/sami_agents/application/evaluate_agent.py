import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass

from sami_agents.application.plan_chat import PlanChat
from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.domain.errors import InvalidModelAnswer, ModelUnavailable
from sami_agents.domain.gateways.chat_model import ChatModel


@dataclass(frozen=True)
class EvalCase:
    message: str
    expected: list[str]
    minimum: int = 1


@dataclass(frozen=True)
class CaseResult:
    case: EvalCase
    status: str
    picks: list[str]
    final: list[str]
    seconds: float
    model_pass: bool
    final_pass: bool


@dataclass(frozen=True)
class Summary:
    cases: int
    answered: int
    model_pass: int
    final_pass: int
    fallback: int
    average_seconds: float
    slowest_seconds: float


def passes(case: EvalCase, ids: list[str]) -> bool:
    if not case.expected:
        return ids == []
    return len(set(ids) & set(case.expected)) >= case.minimum


class RecordingModel(ChatModel):
    def __init__(self, model: ChatModel):
        self.model = model
        self.status = "ok"
        self.raw: list[str] = []
        self.seconds = 0.0

    def pick_widgets(self, message: str, catalog: list[CatalogEntry]) -> list[str]:
        started = time.perf_counter()
        try:
            self.raw = self.model.pick_widgets(message, catalog)
        except ModelUnavailable:
            self.status = "unavailable"
        except InvalidModelAnswer:
            self.status = "invalid"
        finally:
            self.seconds = time.perf_counter() - started
        return self.raw


class EvaluateAgent:
    def __init__(self, model: ChatModel, catalog: list[CatalogEntry]):
        self.model = model
        self.catalog = catalog

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
        recorder = RecordingModel(self.model)
        final = PlanChat(recorder).choose(case.message, self.catalog)
        known = {entry.id for entry in self.catalog}
        picks = list(dict.fromkeys(entry_id for entry_id in recorder.raw if entry_id in known))
        return CaseResult(case, recorder.status, picks, final, recorder.seconds, passes(case, picks), passes(case, final))

    @staticmethod
    def summarise(results: list[CaseResult]) -> Summary:
        seconds = [result.seconds for result in results]
        return Summary(
            cases=len(results),
            answered=sum(result.status == "ok" for result in results),
            model_pass=sum(result.model_pass for result in results),
            final_pass=sum(result.final_pass for result in results),
            fallback=sum(not result.picks for result in results),
            average_seconds=sum(seconds) / len(seconds) if seconds else 0.0,
            slowest_seconds=max(seconds, default=0.0),
        )
