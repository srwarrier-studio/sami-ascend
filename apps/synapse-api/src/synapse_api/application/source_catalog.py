from collections.abc import Callable
from datetime import date

from synapse_api.domain.entities.catalog import CatalogEntry
from synapse_api.domain.errors import CatalogEntryNotFound
from synapse_api.domain.gateways.widget_catalog import WidgetCatalog

TOP = 5


class SourceCatalog(WidgetCatalog):
    def __init__(self, source, build: Callable[[object], list]):
        self.source = source
        self.build = build
        self.widgets = build(source)

    def for_companies(self, companies: tuple[str, ...]) -> "SourceCatalog":
        return SourceCatalog(self.source.for_companies(companies), self.build)

    def entries(self) -> list[CatalogEntry]:
        return [widget.entry for widget in self.widgets]

    def data(self, entry_id: str, today: date, currency: str, top: int = TOP) -> dict:
        for widget in self.widgets:
            if widget.entry.id == entry_id:
                return {**widget.props(today, currency, top), "currency": currency}
        raise CatalogEntryNotFound(entry_id)
