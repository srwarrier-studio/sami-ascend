from decimal import Decimal

MONEY_SCALE = 100
QUANTITY_SCALE = 1000


def to_minor(amount: Decimal, scale: int = MONEY_SCALE) -> int:
    scaled = amount * scale
    if scaled != scaled.to_integral_value():
        raise ValueError(f"{amount} has more decimals than the store keeps")
    return int(scaled)


def from_minor(value: int, scale: int = MONEY_SCALE) -> Decimal:
    digits = len(str(scale)) - 1
    return (Decimal(value) / scale).quantize(Decimal(1).scaleb(-digits))


def quantity_to_minor(quantity: Decimal) -> int:
    return to_minor(quantity, QUANTITY_SCALE)


def quantity_from_minor(value: int) -> Decimal:
    return from_minor(value, QUANTITY_SCALE)
