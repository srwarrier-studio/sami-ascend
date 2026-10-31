from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Drop:
    material: str
    start: date
    end: date
    keep: int
    of: int
    customers: tuple[int, ...] | None = None


@dataclass(frozen=True)
class ContractEnd:
    customer: int
    last_valid: date
    renewal: date | None = None
    renewal_contract: str | None = None
    spot: bool = False


@dataclass(frozen=True)
class SupplyDelay:
    raw_material: str
    month: date
    days: int
    drop: Drop | None = None


@dataclass(frozen=True)
class ProductionDelay:
    material: str
    month: date
    days: int
    reason: str
    drop: Drop | None = None


@dataclass(frozen=True)
class PriceChange:
    material: str
    factor: str
    start: date


@dataclass(frozen=True)
class CustomerLoss:
    customer: int
    start: date


@dataclass(frozen=True)
class Cancellations:
    customer: int
    cancelled: int
    of: int
    start: date
    end: date


@dataclass(frozen=True)
class PurchasePriceChange:
    raw_material: str
    factor: str
    start: date


@dataclass(frozen=True)
class PurchaseQuantityChange:
    raw_material: str
    factor: str
    start: date
    end: date


@dataclass(frozen=True)
class DemandGrowth:
    material: str
    factor: str
    start: date


@dataclass(frozen=True)
class SupplierSwitch:
    raw_material: str
    supplier: int
    price_factor: str
    start: date


Event = ContractEnd | SupplyDelay | ProductionDelay | PriceChange | CustomerLoss | Cancellations | PurchasePriceChange | PurchaseQuantityChange | DemandGrowth | SupplierSwitch


@dataclass(frozen=True)
class Scenario:
    name: str
    events: tuple[Event, ...]
    holdout: bool = False
