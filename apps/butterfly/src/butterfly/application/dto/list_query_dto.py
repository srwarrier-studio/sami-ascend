from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ListQuery:
    filter: str | None = None
    select: str | None = None
    orderby: str | None = None
    top: str | None = None
    skip: str | None = None
    count: str | None = None


@dataclass(frozen=True)
class ListResult:
    rows: list[Any]
    total: int | None
    select: list[str] = field(default_factory=list)
    expand: bool = False
