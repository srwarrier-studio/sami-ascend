import operator
from dataclasses import dataclass
from typing import Any

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

    def matches(self, row) -> bool:
        actual = getattr(row, self.attribute)
        return actual is not None and STRING_FUNCTIONS[self.name](actual, self.text)


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
