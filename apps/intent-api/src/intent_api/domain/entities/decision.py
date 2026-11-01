from dataclasses import dataclass


@dataclass(frozen=True)
class Decision:
    choice: str
    probability: float
