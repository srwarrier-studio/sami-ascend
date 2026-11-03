from collections.abc import Iterable

from token_verification import Role

EVERYWHERE = frozenset({Role.MANAGEMENT, Role.ADMIN})


class WidgetAccess:
    def __init__(self, table: dict[str, frozenset[Role]]):
        self.table = table

    def entry_roles(self) -> tuple[Role, ...]:
        union = EVERYWHERE.union(*self.table.values())
        return tuple(sorted(union))

    def allows(self, roles: Iterable[Role], category: str) -> bool:
        return bool((EVERYWHERE | self.table.get(category, frozenset())) & set(roles))

    def missing(self, categories: Iterable[str]) -> list[str]:
        return sorted(set(categories) - self.table.keys())
