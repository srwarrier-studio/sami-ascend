import operator
from dataclasses import dataclass
from typing import Any

from butterfly.application.alpha import external

COMPARISONS = {
    "eq": operator.eq,
    "ne": operator.ne,
    "gt": operator.gt,
    "ge": operator.ge,
    "lt": operator.lt,
    "le": operator.le,
}

STRING_FUNCTIONS = {
    "contains": lambda value, text: text in value,
    "startswith": lambda value, text: value.startswith(text),
}


@dataclass(frozen=True)
class Comparison:
    attribute: str
    operator: str
    value: Any

    def matches(self, row) -> bool:
        actual = getattr(row, self.attribute)
        return actual is not None and COMPARISONS[self.operator](actual, self.value)


@dataclass(frozen=True)
class StringFunction:
    name: str
    attribute: str
    text: str
    alpha: bool = False

    def matches(self, row) -> bool:
        actual = getattr(row, self.attribute)
        if actual is None:
            return False
        shown = [actual, external(actual)] if self.alpha else [actual]
        return any(STRING_FUNCTIONS[self.name](value, self.text) for value in shown)


@dataclass(frozen=True)
class And:
    left: Any
    right: Any

    def matches(self, row) -> bool:
        return self.left.matches(row) and self.right.matches(row)


@dataclass(frozen=True)
class Or:
    left: Any
    right: Any

    def matches(self, row) -> bool:
        return self.left.matches(row) or self.right.matches(row)


@dataclass(frozen=True)
class Not:
    operand: Any

    def matches(self, row) -> bool:
        return not self.operand.matches(row)
