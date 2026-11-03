from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class ExportDay:
    day: date
    count: int
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class DestinationExport:
    day: date
    country: str
    name: str
    count: int
    amount: Decimal
    currency: str


@dataclass(frozen=True)
class ModeExport:
    day: date
    mode: str
    count: int


@dataclass(frozen=True)
class TransitShipment:
    shipment: str
    destination: str
    expected: date
    amount: Decimal
    currency: str
