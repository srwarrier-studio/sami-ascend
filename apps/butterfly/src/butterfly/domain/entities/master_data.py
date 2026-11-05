from dataclasses import dataclass
from decimal import Decimal

USD_DIVISOR = Decimal(80)
LOCAL_CURRENCY = "INR"
CENTS = Decimal("0.01")
SALES_ORGANIZATIONS = {"INA1": "1010", "INA2": "1020", "INA3": "1030"}
PLANT_COMPANIES = {"1000": "INA1", "2000": "INA2", "3000": "INA3"}
PURCHASING_ORGANIZATIONS = {"INA1": "1010", "INA2": "1020", "INA3": "1030"}
DEFAULT_PURCHASING_GROUP = "001"
ISO_UNITS = {"KG": "KGM", "PC": "PCE", "L": "LTR"}


def in_currency(amount: Decimal, currency: str) -> Decimal:
    return amount if currency == "INR" else amount / USD_DIVISOR


def to_local(amount: Decimal, currency: str) -> Decimal:
    return (amount * USD_DIVISOR if currency == "USD" else amount).quantize(CENTS)


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


@dataclass(frozen=True)
class Product:
    material_id: str
    description: str
    unit: str
    material_group: str
    material_type: str
    company_code: str

    @property
    def iso_unit(self) -> str:
        return ISO_UNITS.get(self.unit, self.unit)


@dataclass(frozen=True)
class Supplier:
    supplier_id: str
    name: str
    company_code: str


@dataclass(frozen=True)
class Plant:
    plant: str
    name: str
    company_code: str
