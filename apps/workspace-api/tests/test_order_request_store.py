import threading
from datetime import datetime, timedelta, timezone

from workspace_api.domain.entities.order_request import FAILED, POSTED, QUEUED, SENDING, UNKNOWN, OrderRequest
from workspace_api.domain.errors import StoreUnavailable
from workspace_api.infrastructure.sqlite_order_request_store import SqliteOrderRequestStore

import pytest

T0 = datetime(2026, 10, 31, 9, 0, tzinfo=timezone.utc)


def make(id_, user="u1", status=QUEUED, minutes=0, next_in=0):
    created = T0 + timedelta(minutes=minutes)
    return OrderRequest(id_, user, "SAP_USER", "req-1", {"sold_to_party": "0000100001"}, status, 0, created + timedelta(seconds=next_in), created, created)


def store():
    return SqliteOrderRequestStore(":memory:", clock=lambda: T0 + timedelta(hours=1))


class TestAddAndGet:
    def test_an_order_comes_back_as_saved(self):
        s = store()
        s.add(make("a"))
        got = s.get("a", "u1")
        assert (got.id, got.user, got.sap_username, got.request_id, got.body, got.status, got.attempts) == ("a", "u1", "SAP_USER", "req-1", {"sold_to_party": "0000100001"}, QUEUED, 0)
        assert (got.created_at, got.sales_order, got.details, got.message) == (T0, None, None, None)

    def test_someone_elses_order_is_not_found(self):
        s = store()
        s.add(make("a"))
        assert s.get("a", "u2") is None and s.get("nope", "u1") is None


class TestClaim:
    def test_the_oldest_due_queued_order_is_taken_and_marked_sending(self):
        s = store()
        s.add(make("late", minutes=5))
        s.add(make("early", minutes=1))
        claimed = s.claim_due(T0 + timedelta(minutes=10))
        assert (claimed.id, claimed.status) == ("early", SENDING)
        assert s.get("early", "u1").status == SENDING

    def test_an_order_is_never_claimed_twice(self):
        s = store()
        s.add(make("a"))
        assert s.claim_due(T0) is not None and s.claim_due(T0) is None

    def test_an_order_whose_time_has_not_come_is_left(self):
        s = store()
        s.add(make("a", next_in=60))
        assert s.claim_due(T0) is None
        assert s.claim_due(T0 + timedelta(seconds=60)).id == "a"

    def test_orders_in_other_statuses_are_not_claimed(self):
        s = store()
        for status in (SENDING, POSTED, UNKNOWN, FAILED):
            s.add(make(status, status=status))
        assert s.claim_due(T0 + timedelta(days=1)) is None

    def test_threads_never_claim_the_same_order(self):
        s = store()
        for n in range(30):
            s.add(make(f"o{n:02d}", minutes=n))
        taken = []

        def work():
            while (order := s.claim_due(T0 + timedelta(days=1))) is not None:
                taken.append(order.id)

        threads = [threading.Thread(target=work) for _ in range(4)]
        [t.start() for t in threads]
        [t.join() for t in threads]
        assert sorted(taken) == [f"o{n:02d}" for n in range(30)]


class TestUpdate:
    def test_fields_change_and_updated_at_moves(self):
        s = store()
        s.add(make("a"))
        s.update("a", status=POSTED, sales_order="0000012031", attempts=2, message="done")
        got = s.get("a", "u1")
        assert (got.status, got.sales_order, got.attempts, got.message, got.updated_at) == (POSTED, "0000012031", 2, "done", T0 + timedelta(hours=1))

    def test_details_and_the_next_try_round_trip(self):
        s = store()
        s.add(make("a"))
        details = [{"code": "CUSTOMER_UNKNOWN", "target": "SoldToParty", "message": "x"}]
        s.update("a", details=details, next_attempt_at=T0 + timedelta(minutes=3))
        got = s.get("a", "u1")
        assert (got.details, got.next_attempt_at) == (details, T0 + timedelta(minutes=3))

    def test_only_the_named_fields_change(self):
        s = store()
        s.add(make("a"))
        s.update("a", message="hello")
        assert s.get("a", "u1").status == QUEUED

    def test_an_unknown_field_is_refused(self):
        s = store()
        s.add(make("a"))
        with pytest.raises(AssertionError):
            s.update("a", user="u2")


class TestRecovery:
    def test_orders_left_sending_become_unknown_with_a_message(self):
        s = store()
        s.add(make("a", status=SENDING))
        s.add(make("b"))
        assert s.recover_sending() == 1
        a = s.get("a", "u1")
        assert a.status == UNKNOWN and "check SAP" in a.message
        assert s.get("b", "u1").status == QUEUED

    def test_orders_survive_a_restart(self, tmp_path):
        path = str(tmp_path / "orders.db")
        SqliteOrderRequestStore(path).add(make("a"))
        again = SqliteOrderRequestStore(path)
        assert again.get("a", "u1").id == "a" and again.claim_due(T0).id == "a"


class TestListOpen:
    def test_only_the_users_open_orders_newest_first(self):
        s = store()
        s.add(make("old", minutes=1))
        s.add(make("new", minutes=9, status=UNKNOWN))
        s.add(make("done", minutes=5, status=POSTED))
        s.add(make("theirs", user="u2", minutes=7))
        s.add(make("broken", minutes=3, status=FAILED))
        assert [r.id for r in s.list_open("u1", 50)] == ["new", "broken", "old"]

    def test_the_limit_is_applied(self):
        s = store()
        for n in range(5):
            s.add(make(f"o{n}", minutes=n))
        assert [r.id for r in s.list_open("u1", 2)] == ["o4", "o3"]


class TestFailure:
    def test_a_broken_database_is_store_unavailable(self):
        s = store()
        s.db.close()
        with pytest.raises(StoreUnavailable):
            s.get("a", "u1")
        with pytest.raises(StoreUnavailable):
            s.claim_due(T0)
