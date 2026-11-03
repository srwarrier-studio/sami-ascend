from dataclasses import dataclass, field


@dataclass(frozen=True)
class BoardWidget:
    id: str
    catalog_id: str
    size: str | None = None


@dataclass(frozen=True)
class Board:
    id: str
    owner_id: str
    owner_name: str
    name: str
    is_public: bool = False
    widgets: list[BoardWidget] = field(default_factory=list)
