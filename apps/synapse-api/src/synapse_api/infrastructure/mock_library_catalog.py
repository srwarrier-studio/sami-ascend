import json
from datetime import date
from pathlib import Path

from synapse_api.domain.entities.catalog import CatalogEntry
from synapse_api.domain.errors import CatalogEntryNotFound
from synapse_api.domain.gateways.widget_catalog import WidgetCatalog

LIBRARY_FILE = Path(__file__).with_name("mock_library.json")


class MockLibraryCatalog(WidgetCatalog):
    def __init__(self, items: list[dict] | None = None):
        items = json.loads(LIBRARY_FILE.read_text()) if items is None else items
        self.items = {item["id"]: item for item in items}

    def entries(self) -> list[CatalogEntry]:
        return [CatalogEntry(i["id"], i["title"], i["description"], i["category"], i["widget"]) for i in self.items.values()]

    def data(self, entry_id: str, today: date) -> dict:
        if entry_id not in self.items:
            raise CatalogEntryNotFound(entry_id)
        return self.items[entry_id]["props"]
