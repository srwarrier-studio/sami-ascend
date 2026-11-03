from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class ExportShipment:
    shipment: str
    sales_order: str
    sold_to_party: str
    customer_name: str | None
    country: str
    country_name: str | None
    transport_mode: str
    shipment_date: date
    expected_arrival_date: date
    actual_arrival_date: date | None
    shipment_status: str
    net_amount: Decimal
    currency: str
    document_amount: Decimal
    document_currency: str
    company_code: str


@dataclass(frozen=True)
class ExportSummaryByDay:
    shipment_date: date
    shipment_count: int
    net_amount: Decimal
    currency: str
    company_code: str


@dataclass(frozen=True)
class ExportSummaryByDestination:
    shipment_date: date
    country: str
    country_name: str | None
    shipment_count: int
    net_amount: Decimal
    currency: str
    company_code: str


@dataclass(frozen=True)
class ExportSummaryByMode:
    shipment_date: date
    transport_mode: str
    shipment_count: int
    company_code: str
