from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Any, Callable

from butterfly.application.delivery_date import TARGET, check_delivery_date
from butterfly.application.usecase.create_sales_order import utc_now
from butterfly.application.usecase.get_sales_order import GetSalesOrder
from butterfly.domain.entities.sales_order import SalesOrder
from butterfly.domain.errors import (
    ETagMismatch,
    ETagRequired,
    ValidationDetail,
    ValidationFailed,
)
from butterfly.domain.repositories.sales_order_repo import SalesOrderRepo

LOCKED_STATUSES = {"C", "X"}


class ChangeSalesOrder:
    def __init__(self, repo: SalesOrderRepo, now: Callable[[], datetime] = utc_now):
        self.repo = repo
        self.now = now

    def execute(self, sales_order: str, if_match: str | None, body: dict[str, Any]) -> SalesOrder:
        order = GetSalesOrder(self.repo).execute(sales_order)
        if if_match is None:
            raise ETagRequired()
        if if_match != order.etag:
            raise ETagMismatch()
        moment = self.now().astimezone(timezone.utc).replace(microsecond=0)
        delivery_date, details = self.validate(order, body, moment.date())
        if details:
            raise ValidationFailed(details)
        changed = replace(
            order,
            requested_delivery_date=delivery_date,
            last_change_date_time=max(moment, order.last_change_date_time + timedelta(seconds=1)),
        )
        self.repo.update(changed)
        return changed

    def validate(self, order: SalesOrder, body: dict, today):
        details = []
        if order.overall_status in LOCKED_STATUSES:
            details.append(
                ValidationDetail(
                    "ORDER_NOT_CHANGEABLE",
                    f"Sales order {order.sales_order} has status {order.overall_status} "
                    "and cannot be changed.",
                    "SalesOrder",
                )
            )
        for name in body:
            if name != TARGET:
                details.append(
                    ValidationDetail(
                        "FIELD_NOT_ALLOWED", f"{name} cannot be changed.", name
                    )
                )
        delivery_date = None
        if body.get(TARGET) is None:
            details.append(
                ValidationDetail("FIELD_REQUIRED", "RequestedDeliveryDate is required.", TARGET)
            )
        else:
            delivery_date, detail = check_delivery_date(body[TARGET], today)
            if detail is not None:
                details.append(detail)
        return delivery_date, details
