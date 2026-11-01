from dataclasses import dataclass

NOTHING_SCENARIO = "nothing"


@dataclass(frozen=True)
class Family:
    id: str
    domain: str
    scenario: str | None
    nothing: bool
    templates: tuple[str, ...]
    heldout: bool
    domain_item: bool = True


@dataclass(frozen=True)
class TrainingItem:
    kind: str
    text: str
    answer: str
    offered: tuple[str, ...]
    families: tuple[str, ...]
    heldout: bool
