from collections.abc import Callable
from datetime import date
from decimal import Decimal

import httpx

from synapse_api.domain.entities.sales import CustomerSales, DailySales, HighValueOrder, MaterialSales, OrderStatus
from synapse_api.domain.gateways.sales_source import SalesSource
from synapse_api.infrastructure.butterfly_sales_mapper import (
    customer_from_json,
    daily_from_json,
    order_from_json,
    material_from_json,
    status_from_json,
)
from synapse_api.infrastructure.odata_reader import ODataReader, company_clause
from synapse_api.infrastructure.settings import Settings


class ButterflySalesSource(SalesSource):
    def __init__(self, settings: Settings, transport: httpx.BaseTransport | None = None, companies: tuple[str, ...] | None = None, reader: ODataReader | None = None):
        self.settings = settings
        self.transport = transport
        self.companies = companies
        self.reader = reader or ODataReader(settings.sap_base_url, settings.sap_timeout_seconds, transport)

    def for_companies(self, companies: tuple[str, ...]) -> "ButterflySalesSource":
        return ButterflySalesSource(self.settings, self.transport, companies, self.reader)

    def daily_sales(self, start: date, end: date) -> list[DailySales]:
        return self.summary("SalesSummaryByDay", "OrderDate,Currency,CompanyCode", start, end, daily_from_json)

    def customer_sales(self, start: date, end: date) -> list[CustomerSales]:
        return self.summary("SalesSummaryByCustomer", "OrderDate,SoldToParty,Currency,CompanyCode", start, end, customer_from_json)

    def material_sales(self, start: date, end: date) -> list[MaterialSales]:
        return self.summary("SalesSummaryByMaterial", "OrderDate,Material,Currency,CompanyCode", start, end, material_from_json)

    def order_statuses(self, start: date, end: date) -> list[OrderStatus]:
        filter_ = f"OrderDate%20ge%20{start.isoformat()}%20and%20OrderDate%20le%20{end.isoformat()}%20and%20OverallStatus%20ne%20'X'{company_clause('CompanyCode', self.companies)}"
        rows = self.reader.all_rows(f"SalesOrder?$filter={filter_}&$select=OrderDate,OverallStatus&$orderby=OrderDate")
        return [status_from_json(row) for row in rows]

    def high_value_orders(self, minimum: Decimal, top: int) -> list[HighValueOrder]:
        filter_ = f"TotalNetAmountLocal%20ge%20{minimum}%20and%20OverallStatus%20ne%20'X'{company_clause('CompanyCode', self.companies)}"
        path = f"SalesOrder?$filter={filter_}&$orderby=CreationDateTime%20desc&$top={top}"
        return [order_from_json(row) for row in self.reader.get_rows(path)]

    def summary(self, entity: str, order: str, start: date, end: date, to_row: Callable[[dict], object]) -> list:
        filter_ = f"OrderDate%20ge%20{start.isoformat()}%20and%20OrderDate%20le%20{end.isoformat()}{company_clause('CompanyCode', self.companies)}"
        return [to_row(row) for row in self.reader.all_rows(f"{entity}?$filter={filter_}&$orderby={order}")]
