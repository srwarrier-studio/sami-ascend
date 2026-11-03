import tomllib
from pathlib import Path

from token_verification import Role

from synapse_api.domain.entities.widget_access import WidgetAccess


def load_widget_access(path: Path) -> WidgetAccess:
    with path.open("rb") as file:
        raw = tomllib.load(file)["access"]
    return WidgetAccess({category: frozenset(Role(name) for name in names) for category, names in raw.items()})
