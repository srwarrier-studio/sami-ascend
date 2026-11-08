from dataclasses import dataclass
from typing import Iterable

from butterfly.domain.errors import NumberRangeFull


@dataclass(frozen=True)
class NumberRange:
    first: int
    last: int
    per_year: bool = False

    def next(self, taken: Iterable[str]) -> str:
        highest = max((int(number) for number in taken), default=self.first - 1)
        number = max(highest, self.first - 1) + 1
        if number > self.last:
            raise NumberRangeFull(f"The number range {self.first} to {self.last} is full")
        return str(number)


PURCHASE_REQUISITION = NumberRange(10000000, 19999999)
PURCHASE_ORDER = NumberRange(4500000001, 4599999999)
MATERIAL_DOCUMENT = NumberRange(4900000000, 4999999999, per_year=True)
SUPPLIER_INVOICE = NumberRange(5100000000, 5199999999, per_year=True)
SALES_ORDER = NumberRange(1, 9999999999)
CUSTOMER = NumberRange(200000, 299999)
