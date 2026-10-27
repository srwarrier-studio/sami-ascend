import re
from datetime import date, datetime, timezone
from decimal import Decimal

from butterfly.application.filter.fields import SALES_ORDER_FIELDS, FieldType
from butterfly.application.filter.nodes import (
    COMPARISONS,
    STRING_FUNCTIONS,
    And,
    Comparison,
    Not,
    Or,
    StringFunction,
)
from butterfly.domain.errors import InvalidQuery

TARGET = "$filter"

TOKEN = re.compile(
    r"""\s*(?:
    (?P<datetime>\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z)
    |(?P<date>\d{4}-\d{2}-\d{2})
    |(?P<number>-?\d+(?:\.\d+)?)
    |(?P<string>'(?:[^']|'')*')
    |(?P<ident>[A-Za-z_]\w*)
    |(?P<symbol>[(),])
    )""",
    re.VERBOSE,
)

LITERAL_TYPES = {
    "string": FieldType.STRING,
    "date": FieldType.DATE,
    "datetime": FieldType.DATETIME,
    "number": FieldType.DECIMAL,
}


def tokenize(text: str) -> list[tuple[str, str]]:
    tokens = []
    position = 0
    while text[position:].strip():
        match = TOKEN.match(text, position)
        if match is None:
            raise InvalidQuery(f"Unexpected text at position {position} in $filter.", TARGET)
        kind = match.lastgroup
        tokens.append((match.group(kind), kind))
        position = match.end()
    return tokens


def literal_value(text: str, kind: str):
    try:
        if kind == "string":
            return text[1:-1].replace("''", "'")
        if kind == "date":
            return date.fromisoformat(text)
        if kind == "datetime":
            return datetime.fromisoformat(text).astimezone(timezone.utc)
        return Decimal(text)
    except ValueError:
        raise InvalidQuery(f"Invalid value {text} in $filter.", TARGET)


class Parser:
    def __init__(self, text: str):
        self.tokens = tokenize(text)
        self.position = 0

    def parse(self):
        if not self.tokens:
            raise InvalidQuery("$filter is empty.", TARGET)
        node = self.parse_or()
        if self.position < len(self.tokens):
            raise InvalidQuery(f"Unexpected {self.tokens[self.position][0]} in $filter.", TARGET)
        return node

    def peek(self) -> tuple[str, str]:
        if self.position >= len(self.tokens):
            return ("", "end")
        return self.tokens[self.position]

    def take(self) -> tuple[str, str]:
        token = self.peek()
        if token[1] == "end":
            raise InvalidQuery("$filter ends too early.", TARGET)
        self.position += 1
        return token

    def expect(self, symbol: str):
        token = self.take()
        if token[0] != symbol or token[1] != "symbol":
            raise InvalidQuery(f"Expected {symbol} but found {token[0]} in $filter.", TARGET)

    def accept_word(self, word: str) -> bool:
        if self.peek() == (word, "ident"):
            self.position += 1
            return True
        return False

    def parse_or(self):
        node = self.parse_and()
        while self.accept_word("or"):
            node = Or(node, self.parse_and())
        return node

    def parse_and(self):
        node = self.parse_not()
        while self.accept_word("and"):
            node = And(node, self.parse_not())
        return node

    def parse_not(self):
        if self.accept_word("not"):
            return Not(self.parse_not())
        return self.parse_primary()

    def parse_primary(self):
        if self.peek() == ("(", "symbol"):
            self.position += 1
            node = self.parse_or()
            self.expect(")")
            return node
        name, kind = self.peek()
        if kind == "ident" and name in STRING_FUNCTIONS:
            return self.parse_function()
        return self.parse_comparison()

    def parse_field(self) -> tuple[str, FieldType]:
        name, kind = self.take()
        if kind != "ident" or name not in SALES_ORDER_FIELDS:
            raise InvalidQuery(f"Unknown field {name} in $filter.", TARGET)
        return SALES_ORDER_FIELDS[name]

    def parse_function(self):
        function = self.take()[0]
        self.expect("(")
        attribute, field_type = self.parse_field()
        if field_type is not FieldType.STRING:
            raise InvalidQuery(f"{function}() works only on text fields.", TARGET)
        self.expect(",")
        text, kind = self.take()
        if kind != "string":
            raise InvalidQuery(f"{function}() needs a text value in quotes.", TARGET)
        self.expect(")")
        return StringFunction(function, attribute, literal_value(text, kind))

    def parse_comparison(self):
        attribute, field_type = self.parse_field()
        name, kind = self.take()
        if kind != "ident" or name not in COMPARISONS:
            raise InvalidQuery(f"Unknown operator {name} in $filter.", TARGET)
        text, kind = self.take()
        if LITERAL_TYPES.get(kind) is not field_type:
            raise InvalidQuery(f"Value {text} does not match the field type in $filter.", TARGET)
        return Comparison(attribute, name, literal_value(text, kind))


def parse_filter(text: str):
    return Parser(text).parse()
