from pydantic import BaseModel

from synapse_api.domain.entities.catalog import CatalogEntry


class CatalogEntryResponse(BaseModel):
    id: str
    title: str
    description: str
    category: str
    widget: str


class CatalogResponse(BaseModel):
    entries: list[CatalogEntryResponse]

    @classmethod
    def from_domain(cls, entries: list[CatalogEntry]) -> "CatalogResponse":
        return cls.model_validate({"entries": entries}, from_attributes=True)
