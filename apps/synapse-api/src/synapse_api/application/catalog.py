from datetime import date

from synapse_api.domain.entities.catalog import CatalogEntry
from synapse_api.domain.gateways.widget_catalog import WidgetCatalog


class ListCatalog:
    def __init__(self, catalog: WidgetCatalog):
        self.catalog = catalog

    def execute(self) -> list[CatalogEntry]:
        return self.catalog.entries()


class GetWidgetData:
    def __init__(self, catalog: WidgetCatalog):
        self.catalog = catalog

    def execute(self, entry_id: str, today: date) -> dict:
        return self.catalog.data(entry_id, today)
