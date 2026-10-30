from dataclasses import dataclass


@dataclass(frozen=True)
class CatalogEntry:
    id: str
    title: str
    description: str
