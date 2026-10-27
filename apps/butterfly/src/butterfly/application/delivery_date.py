import re
from datetime import date
from typing import Any

from butterfly.domain.errors import ValidationDetail

DATE_FORMAT = re.compile(r"\d{4}-\d{2}-\d{2}")
TARGET = "RequestedDeliveryDate"


def check_delivery_date(value: Any, today: date) -> tuple[date | None, ValidationDetail | None]:
    try:
        if not isinstance(value, str) or not DATE_FORMAT.fullmatch(value):
            raise ValueError
        parsed = date.fromisoformat(value)
    except ValueError:
        return None, ValidationDetail(
            "FIELD_INVALID", "RequestedDeliveryDate must be a date like 2026-11-05.", TARGET
        )
    if parsed < today:
        return parsed, ValidationDetail(
            "DELIVERY_DATE_IN_PAST", "RequestedDeliveryDate must not be before today.", TARGET
        )
    return parsed, None
