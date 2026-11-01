from dataclasses import dataclass

SLOTS = ("period", "entity", "top")


@dataclass(frozen=True)
class Scenario:
    id: str
    domain: str
    description: str
    examples: tuple[str, ...]
    needs: tuple[str, ...] = ()
    covers: tuple[str, ...] = ()


@dataclass(frozen=True)
class Library:
    domains: dict[str, str]
    scenarios: dict[str, Scenario]
