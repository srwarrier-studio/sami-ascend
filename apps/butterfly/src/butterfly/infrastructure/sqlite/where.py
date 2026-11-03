import re
from datetime import date, datetime, timezone
from decimal import Decimal

from butterfly.application.filter.nodes import And, Comparison, Not, Or, StringFunction

OPERATORS = {"eq": "=", "ne": "!=", "gt": ">", "ge": ">=", "lt": "<", "le": "<="}
NAME = re.compile(r"^[a-z][a-z0-9_]*$")


def column(attribute: str) -> str:
    if not NAME.match(attribute):
        raise ValueError(f"not a column name: {attribute}")
    return attribute


def bound(value, scale: int | None):
    if isinstance(value, Decimal):
        return str(value * scale) if scale else str(value)
    if isinstance(value, datetime):
        return value.astimezone(timezone.utc).isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return value


def where(node, scales: dict[str, int]) -> tuple[str, list]:
    if isinstance(node, Comparison):
        name = column(node.attribute)
        return f"COALESCE({name} {OPERATORS[node.operator]} ?, 0)", [bound(node.value, scales.get(name))]
    if isinstance(node, StringFunction):
        name = column(node.attribute)
        if node.name == "contains":
            return f"COALESCE(instr({name}, ?) > 0, 0)", [node.text]
        return f"COALESCE(substr({name}, 1, length(?)) = ?, 0)", [node.text, node.text]
    if isinstance(node, Not):
        sql, params = where(node.operand, scales)
        return f"(NOT {sql})", params
    left, left_params = where(node.left, scales)
    right, right_params = where(node.right, scales)
    joiner = "AND" if isinstance(node, And) else "OR"
    return f"({left} {joiner} {right})", left_params + right_params
