from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.domain.errors import CatalogUnavailable
from sami_agents.domain.gateways.catalog_source import CatalogSource

DEFAULT_ENTRIES = [
    CatalogEntry("sales-today", "Sales today", "Net sales invoiced today against yesterday."),
    CatalogEntry("sales-month", "Sales this month", "Net sales invoiced this month against last month."),
    CatalogEntry("top-customers", "Top customers", "Customers ranked by net sales this month."),
    CatalogEntry("top-materials", "Top materials", "Materials ranked by net sales this month."),
    CatalogEntry("day-sales", "Day sales", "Net sales for each day of this month, with last month behind it."),
]


class MockCatalogSource(CatalogSource):
    def __init__(self, entries: list[CatalogEntry] | None = None, unavailable: bool = False):
        self._entries = DEFAULT_ENTRIES if entries is None else entries
        self.unavailable = unavailable
        self.tokens: list[str] = []

    def entries(self, access_token: str) -> list[CatalogEntry]:
        self.tokens.append(access_token)
        if self.unavailable:
            raise CatalogUnavailable()
        return list(self._entries)
