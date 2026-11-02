from dataclasses import dataclass
from decimal import Decimal

USD_DIVISOR = Decimal(80)


def in_currency(amount: Decimal, currency: str) -> Decimal:
    return amount if currency == "INR" else amount / USD_DIVISOR


@dataclass(frozen=True)
class Customer:
    customer_id: str
    name: str
    country: str = "IN"
    company_code: str = "INA1"


@dataclass(frozen=True)
class Material:
    material_id: str
    description: str
    unit: str
    price: Decimal
    company_code: str = "INA1"

    def price_in(self, currency: str) -> Decimal:
        return in_currency(self.price, currency)
