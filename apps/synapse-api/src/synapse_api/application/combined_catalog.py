from datetime import date

from synapse_api.domain.entities.catalog import CatalogEntry
from synapse_api.domain.errors import CatalogEntryNotFound
from synapse_api.domain.gateways.widget_catalog import WidgetCatalog


class CombinedCatalog(WidgetCatalog):
    def __init__(self, *catalogs: WidgetCatalog):
        self.catalogs = catalogs

    def entries(self) -> list[CatalogEntry]:
        return [entry for catalog in self.catalogs for entry in catalog.entries()]

    def data(self, entry_id: str, today: date) -> dict:
        for catalog in self.catalogs:
            if any(entry.id == entry_id for entry in catalog.entries()):
                return catalog.data(entry_id, today)
        raise CatalogEntryNotFound(entry_id)
