from dataclasses import dataclass


@dataclass(frozen=True)
class EvalCase:
    id: str
    question: str
    part: str
    domain: str
    scenarios: frozenset[str]
    heldout: bool

    @property
    def should_answer(self) -> bool:
        return bool(self.scenarios)
