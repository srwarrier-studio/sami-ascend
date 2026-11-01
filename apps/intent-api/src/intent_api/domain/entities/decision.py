from dataclasses import dataclass, field


@dataclass(frozen=True)
class Decision:
    choice: str
    probability: float
    scores: dict[str, float] = field(default_factory=dict, compare=False)
