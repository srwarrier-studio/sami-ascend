from dataclasses import dataclass

RESPONSES = ("value", "compare", "trend", "ranking")
AGAINST = ("previous", "last_year")


@dataclass(frozen=True)
class AnswerRule:
    scenario: str
    response: str
    metric: str
    by: str | None = None
    against: str | None = None


@dataclass(frozen=True)
class Block:
    type: str
    data: dict


@dataclass(frozen=True)
class Answer:
    scenario: str
    blocks: tuple[Block, ...]
