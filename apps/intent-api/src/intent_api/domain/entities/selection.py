from dataclasses import dataclass


@dataclass(frozen=True)
class Selected:
    scenario: str
    probability: float
    clause: str
