from dataclasses import replace
from datetime import date, datetime, timedelta, timezone

import pytest

from butterfly.application.usecase.change_sales_order import ChangeSalesOrder
from butterfly.domain.errors import ETagMismatch, ETagRequired, SalesOrderNotFound, ValidationFailed
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo
from conftest import NOW, ORDERS


def order_with_status(status):
    return next(o for o in ORDERS if o.overall_status == status)


OPEN = order_with_status("A")
IN_PROCESS = order_with_status("B")
COMPLETED = order_with_status("C")
CANCELLED = order_with_status("X")
NEW_DATE = {"RequestedDeliveryDate": "2026-12-01"}


def make(now=NOW):
    repo = InMemorySalesOrderRepo(list(ORDERS))
    return repo, ChangeSalesOrder(repo, lambda: now)


def problems(order, body, now=NOW):
    repo, use_case = make(now)
    with pytest.raises(ValidationFailed) as error:
        use_case.execute(order.sales_order, order.etag, body)
    assert repo.get(order.sales_order) == order
    return [(d.code, d.target) for d in error.value.details]


class TestChangeSalesOrder:
    def setup_method(self):
        self.repo, self.use_case = make()
        self.changed = self.use_case.execute(OPEN.sales_order, OPEN.etag, NEW_DATE)

    def test_sets_the_new_delivery_date(self):
        assert self.changed.requested_delivery_date == date(2026, 12, 1)

    def test_is_stored(self):
        assert self.repo.get(OPEN.sales_order) == self.changed

    def test_nothing_else_changes_except_the_change_time(self):
        assert replace(self.changed, requested_delivery_date=OPEN.requested_delivery_date,
                       last_change_date_time=OPEN.last_change_date_time) == OPEN

    def test_items_and_creation_time_are_kept(self):
        assert self.changed.items == OPEN.items
        assert self.changed.creation_date_time == OPEN.creation_date_time

    def test_change_time_is_now(self):
        assert self.changed.last_change_date_time == NOW

    def test_other_orders_are_untouched(self):
        others = [o for o in self.repo.list_all() if o.sales_order != OPEN.sales_order]

        assert others == [o for o in ORDERS if o.sales_order != OPEN.sales_order]

    def test_in_process_order_can_be_changed(self):
        _, use_case = make()

        changed = use_case.execute(IN_PROCESS.sales_order, IN_PROCESS.etag, NEW_DATE)

        assert changed.requested_delivery_date == date(2026, 12, 1)

    def test_order_that_had_no_date_can_get_one(self):
        empty = next(o for o in ORDERS if o.requested_delivery_date is None and o.overall_status in "AB")
        _, use_case = make()

        assert use_case.execute(empty.sales_order, empty.etag, NEW_DATE).requested_delivery_date

    def test_today_is_accepted(self):
        _, use_case = make()

        changed = use_case.execute(OPEN.sales_order, OPEN.etag, {"RequestedDeliveryDate": "2026-10-27"})

        assert changed.requested_delivery_date == date(2026, 10, 27)


class TestUnknownOrder:
    def test_is_not_found(self):
        _, use_case = make()

        with pytest.raises(SalesOrderNotFound):
            use_case.execute("0000099999", 'W/"x"', NEW_DATE)

    def test_not_found_wins_over_a_missing_etag(self):
        _, use_case = make()

        with pytest.raises(SalesOrderNotFound):
            use_case.execute("0000099999", None, NEW_DATE)


class TestEtagCheck:
    def test_missing_header_is_required(self):
        _, use_case = make()

        with pytest.raises(ETagRequired):
            use_case.execute(OPEN.sales_order, None, NEW_DATE)

    @pytest.mark.parametrize(
        "value",
        ["", "*", 'W/"0"', "W/20261018090000", OPEN.etag.removeprefix("W/"), OPEN.etag.lower() + " ", ORDERS[1].etag],
        ids=["empty", "star", "wrong stamp", "no quotes", "no weak prefix", "trailing space", "another orders etag"],
    )
    def test_anything_but_the_current_etag_is_a_mismatch(self, value):
        repo, use_case = make()

        with pytest.raises(ETagMismatch):
            use_case.execute(OPEN.sales_order, value, NEW_DATE)
        assert repo.get(OPEN.sales_order) == OPEN

    def test_etag_is_checked_before_the_body(self):
        _, use_case = make()

        with pytest.raises(ETagMismatch):
            use_case.execute(OPEN.sales_order, 'W/"0"', {"Colour": "red"})


class TestEtagAlwaysChanges:
    def test_change_in_the_same_second_as_the_creation_still_changes_the_etag(self):
        _, use_case = make(now=OPEN.last_change_date_time)

        changed = use_case.execute(OPEN.sales_order, OPEN.etag, NEW_DATE)

        assert changed.etag != OPEN.etag
        assert changed.last_change_date_time == OPEN.last_change_date_time + timedelta(seconds=1)

    def test_two_changes_in_one_second_get_different_etags(self):
        _, use_case = make()

        first = use_case.execute(OPEN.sales_order, OPEN.etag, NEW_DATE)
        second = use_case.execute(OPEN.sales_order, first.etag, {"RequestedDeliveryDate": "2026-12-02"})

        assert len({OPEN.etag, first.etag, second.etag}) == 3

    def test_old_etag_is_refused_after_a_change(self):
        _, use_case = make()
        use_case.execute(OPEN.sales_order, OPEN.etag, NEW_DATE)

        with pytest.raises(ETagMismatch):
            use_case.execute(OPEN.sales_order, OPEN.etag, {"RequestedDeliveryDate": "2026-12-02"})

    def test_clock_running_behind_still_moves_forward(self):
        behind = OPEN.last_change_date_time - timedelta(days=1)
        _, use_case = make(now=behind)

        changed = use_case.execute(OPEN.sales_order, OPEN.etag, NEW_DATE)

        assert changed.last_change_date_time > OPEN.last_change_date_time


class TestOrderStatus:
    @pytest.mark.parametrize("order", [COMPLETED, CANCELLED], ids=["completed", "cancelled"])
    def test_completed_and_cancelled_orders_cannot_be_changed(self, order):
        assert problems(order, NEW_DATE) == [("ORDER_NOT_CHANGEABLE", "SalesOrder")]

    def test_not_changeable_is_reported_together_with_body_problems(self):
        assert problems(COMPLETED, {"RequestedDeliveryDate": "2020-01-01"}) == [
            ("ORDER_NOT_CHANGEABLE", "SalesOrder"),
            ("DELIVERY_DATE_IN_PAST", "RequestedDeliveryDate"),
        ]


class TestBody:
    @pytest.mark.parametrize("body", [{}, {"RequestedDeliveryDate": None}], ids=["missing", "null"])
    def test_date_is_required(self, body):
        assert problems(OPEN, body) == [("FIELD_REQUIRED", "RequestedDeliveryDate")]

    def test_yesterday_is_in_the_past(self):
        assert problems(OPEN, {"RequestedDeliveryDate": "2026-10-26"}) == [
            ("DELIVERY_DATE_IN_PAST", "RequestedDeliveryDate")
        ]

    @pytest.mark.parametrize("value", ["05-11-2026", "2026-02-30", "", "soon", 20261105, True])
    def test_wrong_format(self, value):
        assert problems(OPEN, {"RequestedDeliveryDate": value}) == [
            ("FIELD_INVALID", "RequestedDeliveryDate")
        ]

    @pytest.mark.parametrize("name", ["CustomerName", "SoldToParty", "TotalNetAmount", "Colour", "SalesOrder"])
    def test_other_fields_cannot_be_changed(self, name):
        assert problems(OPEN, {**NEW_DATE, name: "x"}) == [("FIELD_NOT_ALLOWED", name)]

    def test_status_cannot_be_set_through_a_change(self):
        assert problems(OPEN, {**NEW_DATE, "OverallStatus": "X"}) == [("FIELD_NOT_ALLOWED", "OverallStatus")]

    def test_items_cannot_be_changed(self):
        assert problems(OPEN, {**NEW_DATE, "_Item": []}) == [("FIELD_NOT_ALLOWED", "_Item")]

    def test_empty_body_with_a_wrong_field_reports_both(self):
        assert problems(OPEN, {"Colour": "red"}) == [
            ("FIELD_NOT_ALLOWED", "Colour"),
            ("FIELD_REQUIRED", "RequestedDeliveryDate"),
        ]
