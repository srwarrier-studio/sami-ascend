from datetime import date
from decimal import Decimal

from synapse_api.domain.entities.receivables import AgeBucket, CustomerReceivable, ReceivablesTotal
from synapse_api.domain.gateways.receivables_source import ReceivablesSource
from synapse_api.infrastructure.odata_reader import ODataReader, company_clause

COMPANY_CLAUSE_PREFIX = "%20and%20"


class ButterflyReceivablesSource(ReceivablesSource):
    def __init__(self, reader: ODataReader, companies: tuple[str, ...] | None = None):
        self.reader = reader
        self.companies = companies

    def for_companies(self, companies: tuple[str, ...]) -> "ButterflyReceivablesSource":
        return ButterflyReceivablesSource(self.reader, companies)

    def path(self, entity: str, as_of: date, order: str) -> str:
        clause = company_clause("CompanyCode", self.companies).removeprefix(COMPANY_CLAUSE_PREFIX)
        filter_ = f"&$filter={clause}" if clause else ""
        return f"{entity}?AsOfDate={as_of.isoformat()}{filter_}&$orderby={order}"

    def totals(self, as_of: date) -> list[ReceivablesTotal]:
        rows = self.reader.all_rows(self.path("ReceivablesSummary", as_of, "AsOfDate,Currency,CompanyCode"))
        return [ReceivablesTotal(r["Currency"], Decimal(r["OpenAmount"]), Decimal(r["OverdueAmount"]), r["OpenCount"], r["OverdueCount"]) for r in rows]

    def by_customer(self, as_of: date) -> list[CustomerReceivable]:
        rows = self.reader.all_rows(self.path("ReceivablesByCustomer", as_of, "AsOfDate,SoldToParty,Currency,CompanyCode"))
        return [CustomerReceivable(r["SoldToParty"], r["CustomerName"] or "", r["Currency"], Decimal(r["OpenAmount"]), Decimal(r["OverdueAmount"])) for r in rows]

    def ageing(self, as_of: date) -> list[AgeBucket]:
        rows = self.reader.all_rows(self.path("ReceivablesAgeing", as_of, "AsOfDate,AgeBucket,Currency,CompanyCode"))
        return [AgeBucket(r["AgeBucket"], r["Currency"], Decimal(r["OpenAmount"]), r["OpenCount"]) for r in rows]
