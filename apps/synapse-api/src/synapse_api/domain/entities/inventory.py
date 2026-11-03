from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class StockItem:
    material: str
    description: str
    quantity: Decimal
    unit: str
    reorder_level: Decimal
    status: str
    last_movement: date | None
    currency: str


@dataclass(frozen=True)
class StatusStock:
    status: str
    value: Decimal
    count: int
    currency: str


@dataclass(frozen=True)
class WarehouseStock:
    plant: str
    location: str
    name: str
    value: Decimal
    count: int
    currency: str


@dataclass(frozen=True)
class GroupStock:
    group: str
    name: str
    value: Decimal
    count: int
    currency: str


@dataclass(frozen=True)
class MonthValue:
    period: str
    value: Decimal
    currency: str


@dataclass(frozen=True)
class DayMovement:
    day: date
    receipts: Decimal
    issues: Decimal
    count: int
    currency: str


@dataclass(frozen=True)
class HourMovement:
    day: date
    hour: int
    count: int
