import threading
from datetime import date
from decimal import Decimal

import httpx
import pytest

from workspace_api.application.throttled_gateway import ThrottledGateway
from workspace_api.domain.entities.sales_order import NewSalesOrder, NewSalesOrderItem
from workspace_api.domain.errors import SapNotReached, SapOutcomeUnknown, SapUnavailable
from workspace_api.infrastructure.butterfly_sales_order_gateway import ButterflySalesOrderGateway
from workspace_api.infrastructure.mock_sales_order_gateway import MockSalesOrderGateway
from workspace_api.infrastructure.settings import Settings

ORDER = NewSalesOrder("OR", "0000100001", "INR", date(2026, 11, 5), [NewSalesOrderItem("RM-1001", Decimal("50.000"), "KG")])


def create_through(handler):
    return ButterflySalesOrderGateway(Settings(sap_base_url="http://sap/root/"), httpx.MockTransport(handler)).create(ORDER)


def raising(error):
    def handler(request):
        raise error

    return handler


class TestNotProcessedForCertain:
    @pytest.mark.parametrize("error", [httpx.ConnectError("refused"), httpx.ConnectTimeout("slow"), httpx.PoolTimeout("busy")])
    def test_a_connection_that_never_opened(self, error):
        with pytest.raises(SapNotReached):
            create_through(raising(error))

    @pytest.mark.parametrize("status", [503, 429])
    def test_an_explicit_refusal(self, status):
        with pytest.raises(SapNotReached):
            create_through(lambda request: httpx.Response(status))


class TestOutcomeUnknown:
    @pytest.mark.parametrize("error", [httpx.ReadTimeout("slow"), httpx.ReadError("broken"), httpx.RemoteProtocolError("cut"), httpx.WriteError("half sent")])
    def test_a_connection_that_failed_after_the_request_was_sent(self, error):
        with pytest.raises(SapOutcomeUnknown):
            create_through(raising(error))

    @pytest.mark.parametrize("status", [500, 502, 504])
    def test_any_other_server_error(self, status):
        with pytest.raises(SapOutcomeUnknown):
            create_through(lambda request: httpx.Response(status))


class TestStillAnSapUnavailable:
    def test_both_kinds_are_caught_by_the_old_handler(self):
        assert issubclass(SapNotReached, SapUnavailable) and issubclass(SapOutcomeUnknown, SapUnavailable)

    def test_an_unexpected_status_stays_a_plain_unavailable(self):
        with pytest.raises(SapUnavailable) as caught:
            create_through(lambda request: httpx.Response(404))
        assert type(caught.value) is SapUnavailable


class Blocking(MockSalesOrderGateway):
    def __init__(self):
        super().__init__()
        self.inside = threading.Event()
        self.release = threading.Event()
        self.fail = False

    def create(self, order):
        self.inside.set()
        self.release.wait(2)
        if self.fail:
            raise SapOutcomeUnknown("boom")
        return super().create(order)


class TestWriteLimit:
    def start_blocked(self, gateway, limit):
        throttled = ThrottledGateway(gateway, limit, 0.05)
        thread = threading.Thread(target=lambda: throttled.create(ORDER))
        thread.start()
        assert gateway.inside.wait(1)
        return throttled, thread

    def test_a_second_write_waits_and_is_not_reached_when_the_only_slot_is_busy(self):
        gateway = Blocking()
        throttled, thread = self.start_blocked(gateway, 1)
        with pytest.raises(SapNotReached):
            throttled.create(ORDER)
        gateway.release.set()
        thread.join()

    def test_with_two_slots_both_writes_go_through(self):
        gateway = Blocking()
        throttled, thread = self.start_blocked(gateway, 2)
        gateway.release.set()
        throttled.create(ORDER)
        thread.join()
        assert len(gateway.orders) == 2

    def test_the_slot_is_released_after_a_failure(self):
        gateway = Blocking()
        gateway.fail = True
        gateway.release.set()
        throttled = ThrottledGateway(gateway, 1, 0.05)
        for _ in range(3):
            with pytest.raises(SapOutcomeUnknown):
                throttled.create(ORDER)

    def test_a_waiting_write_gets_the_slot_when_it_frees_in_time(self):
        gateway = Blocking()
        throttled = ThrottledGateway(gateway, 1, 2)
        thread = threading.Thread(target=lambda: throttled.create(ORDER))
        thread.start()
        assert gateway.inside.wait(1)
        timer = threading.Timer(0.1, gateway.release.set)
        timer.start()
        throttled.create(ORDER)
        thread.join()
        assert len(gateway.orders) == 2

    def test_reads_are_not_limited(self):
        gateway = Blocking()
        throttled, thread = self.start_blocked(gateway, 1)
        assert throttled.list_recent(5, 0).total == 0
        gateway.release.set()
        thread.join()


class TestBusyIsNotReached:
    def test_a_busy_slot_is_its_own_kind_of_not_reached(self):
        from workspace_api.domain.errors import SapBusy

        assert issubclass(SapBusy, SapNotReached)
