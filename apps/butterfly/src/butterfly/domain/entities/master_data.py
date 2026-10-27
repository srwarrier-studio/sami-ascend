from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True)
class Customer:
    customer_id: str
    name: str


@dataclass(frozen=True)
class Material:
    material_id: str
    description: str
    unit: str
    price: Decimal
