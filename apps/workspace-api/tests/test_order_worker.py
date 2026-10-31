import threading
import time
from datetime import datetime, timedelta, timezone

import pytest

from workspace_api.application.order_worker import FIRST_WAIT_SECONDS, OrderWorker, backoff_seconds
from workspace_api.domain.entities.order_request import FAILED, POSTED, QUEUED, REJECTED, UNKNOWN, OrderRequest
from workspace_api.domain.errors import SalesOrderRejected, SapBusy, SapNotReached, SapOutcomeUnknown, SapUnavailable, ValidationDetail
from workspace_api.entrypoint.workers import start_workers
from workspace_api.infrastructure.mock_sales_order_gateway import MockSalesOrderGateway
from workspace_api.infrastructure.sqlite_order_request_store import SqliteOrderRequestStore

T0 = datetime(2026, 10, 31, 9, 0, tzinfo=timezone.utc)
BODY = {"sales_order_type": "OR", "sold_to_party": "0000100001", "transaction_currency": "INR", "requested_delivery_date": "2026-11-05",
        "items": [{"material": "RM-1001", "quantity": "50.000", "quantity_unit": "KG"}]}


class Clock:
    def __init__(self):
        self.now = T0

    def __call__(self):
        return self.now

    def advance(self, seconds):
        self.now += timedelta(seconds=seconds)


def queue(store, id_="a", minutes=0):
    created = T0 + timedelta(minutes=minutes)
    store.add(OrderRequest(id_, "u1", "SAP_USER", "req", BODY, QUEUED, 0, T0, created, created))


def setup(max_attempts=8):
    store, clock, gateway = SqliteOrderRequestStore(":memory:"), Clock(), MockSalesOrderGateway()
    return store, clock, gateway, OrderWorker(store, gateway, max_attempts, clock)


def failing(gateway, *errors):
    queue_of = list(errors)
    real = gateway.create

    def create(order):
        error = queue_of.pop(0) if queue_of else None
        if error:
            raise error
        return real(order)

    gateway.create = create


class TestPosting:
    def test_a_queued_order_is_posted_once_with_the_sap_number(self):
        store, _, gateway, worker = setup()
        queue(store)
        assert worker.run_once() is True
        got = store.get("a", "u1")
        assert (got.status, got.sales_order) == (POSTED, "0000000001")
        assert worker.run_once() is False and len(gateway.orders) == 1

    def test_the_order_is_posted_as_it_was_saved(self):
        store, _, gateway, worker = setup()
        queue(store)
        worker.run_once()
        [order] = gateway.orders
        assert (order.sold_to_party, order.items[0].material, str(order.items[0].quantity), str(order.requested_delivery_date)) == ("0000100001", "RM-1001", "50.000", "2026-11-05")

    def test_a_rejection_is_recorded_with_sap_details_and_not_retried(self):
        store, clock, gateway, worker = setup()
        gateway.reject_with([ValidationDetail("CUSTOMER_UNKNOWN", "x", "SoldToParty")])
        queue(store)
        worker.run_once()
        got = store.get("a", "u1")
        assert (got.status, got.details) == (REJECTED, [{"code": "CUSTOMER_UNKNOWN", "target": "SoldToParty", "message": "x"}])
        clock.advance(86400)
        assert worker.run_once() is False


class TestBackOff:
    def test_the_waits_double_from_30_seconds_up_to_15_minutes(self):
        assert [backoff_seconds(n) for n in range(1, 8)] == [30, 60, 120, 240, 480, 900, 900]

    def test_a_not_processed_failure_comes_back_after_the_wait_and_not_before(self):
        store, clock, gateway, worker = setup()
        failing(gateway, SapNotReached("refused"))
        queue(store)
        worker.run_once()
        got = store.get("a", "u1")
        assert (got.status, got.attempts, got.next_attempt_at) == (QUEUED, 1, T0 + timedelta(seconds=FIRST_WAIT_SECONDS))
        clock.advance(29)
        assert worker.run_once() is False
        clock.advance(1)
        assert worker.run_once() is True and store.get("a", "u1").status == POSTED

    def test_each_failure_waits_twice_as_long(self):
        store, clock, gateway, worker = setup()
        failing(gateway, *[SapNotReached("refused")] * 3)
        queue(store)
        waits = []
        for _ in range(3):
            worker.run_once()
            got = store.get("a", "u1")
            waits.append((got.next_attempt_at - clock.now).seconds)
            clock.now = got.next_attempt_at
        assert waits == [30, 60, 120]

    def test_it_gives_up_as_failed_after_the_last_attempt(self):
        store, clock, gateway, worker = setup(max_attempts=3)
        failing(gateway, *[SapNotReached("refused")] * 5)
        queue(store)
        for _ in range(3):
            worker.run_once()
            clock.advance(3600)
        got = store.get("a", "u1")
        assert (got.status, got.attempts) == (FAILED, 3) and "several tries" in got.message
        assert worker.run_once() is False

    def test_a_busy_slot_waits_a_few_seconds_and_costs_no_attempt(self):
        store, clock, gateway, worker = setup(max_attempts=1)
        failing(gateway, SapBusy("busy"), SapBusy("busy"))
        queue(store)
        for _ in range(2):
            worker.run_once()
            clock.advance(5)
        got = store.get("a", "u1")
        assert (got.status, got.attempts) == (QUEUED, 0)
        worker.run_once()
        assert store.get("a", "u1").status == POSTED


class TestUnknownIsNeverRetried:
    @pytest.mark.parametrize("error", [SapOutcomeUnknown("timeout"), SapUnavailable("odd"), RuntimeError("bug")])
    def test_it_is_marked_unknown_with_a_message_and_left_alone(self, error):
        store, clock, gateway, worker = setup()
        failing(gateway, error)
        queue(store)
        worker.run_once()
        got = store.get("a", "u1")
        assert got.status == UNKNOWN and "Check the order list" in got.message
        clock.advance(86400)
        assert worker.run_once() is False and gateway.orders == []


class TestAtMostOnce:
    def test_whatever_the_failures_an_order_is_posted_at_most_once(self):
        outcomes = [
            [SapNotReached("x"), SapNotReached("x"), None],
            [SapNotReached("x"), SapOutcomeUnknown("x")],
            [SapOutcomeUnknown("x"), None],
            [SalesOrderRejected([ValidationDetail("C", "m", "t")])],
            [None, None],
        ]
        for errors in outcomes:
            store, clock, gateway, worker = setup()
            calls = []
            real = gateway.create

            def create(order, errors=errors, calls=calls, real=real):
                calls.append(1)
                error = errors[len(calls) - 1] if len(calls) <= len(errors) else None
                if error:
                    raise error
                return real(order)

            gateway.create = create
            queue(store)
            for _ in range(20):
                worker.run_once()
                clock.advance(3600)
            assert len(gateway.orders) <= 1
            assert len(calls) == min(len(calls), len(errors))

    def test_two_workers_never_post_the_same_order(self):
        store, clock, gateway, _ = setup()
        for n in range(20):
            queue(store, f"o{n:02d}", minutes=n)
        workers = [OrderWorker(store, gateway, 8, clock) for _ in range(2)]

        def work(worker):
            while worker.run_once():
                pass

        threads = [threading.Thread(target=work, args=(w,)) for w in workers]
        [t.start() for t in threads]
        [t.join() for t in threads]
        assert len(gateway.orders) == 20 and len({o.sales_order for o in gateway.orders}) == 20
        assert all(store.get(f"o{n:02d}", "u1").status == POSTED for n in range(20))


class TestTheLoop:
    def test_workers_post_what_is_queued_and_stop_on_request(self):
        store, clock, gateway, worker = setup()
        queue(store)
        stop = start_workers(worker, 1, idle_seconds=0.01)
        for _ in range(100):
            if store.get("a", "u1").status == POSTED:
                break
            time.sleep(0.01)
        stop.set()
        assert store.get("a", "u1").status == POSTED

    def test_zero_workers_start_nothing(self):
        store, clock, gateway, worker = setup()
        queue(store)
        stop = start_workers(worker, 0, idle_seconds=0.01)
        time.sleep(0.05)
        stop.set()
        assert store.get("a", "u1").status == QUEUED
