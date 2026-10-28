from decimal import Decimal

import pytest
from fastapi.testclient import TestClient
from test_routes_rankings import CUSTOMERS, ORDERS
from test_routes_totals import DAILY, SECRET, TODAY, token_with
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from synapse_api.application.sales_cache import SalesCache
from synapse_api.entrypoint.app import create_app
from synapse_api.infrastructure.mock_sales_source import MockSalesSource
from synapse_api.infrastructure.settings import Settings

BASE = "/v1/synapse/sales"
ROUTES = [
    "today",
    "month-to-date",
    "year-to-date",
    "month-on-month",
    "top-customers",
    "top-materials",
    "high-value-orders",
]


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


def make(source: MockSalesSource, seconds: float = 300):
    clock = Clock()
    app = create_app(source, Settings(jwt_secret=SECRET, _env_file=None), lambda: TODAY, SalesCache(seconds, clock))
    client = TestClient(app)
    client.cookies.set(ACCESS_TOKEN_COOKIE, token_with(["management"]))
    return client, clock


def full_source() -> MockSalesSource:
    return MockSalesSource(DAILY, CUSTOMERS, orders=ORDERS)


class TestCacheHit:
    @pytest.mark.parametrize("route", ROUTES)
    def test_second_call_inside_the_time_does_not_reach_the_source(self, route):
        source = full_source()
        client, clock = make(source)
        first = client.get(f"{BASE}/{route}")
        calls = source.calls
        clock.now = 299
        second = client.get(f"{BASE}/{route}")
        assert second.json() == first.json()
        assert source.calls == calls

    def test_call_after_the_time_reaches_the_source_again(self):
        source = full_source()
        client, clock = make(source)
        client.get(f"{BASE}/today")
        calls = source.calls
        clock.now = 301
        client.get(f"{BASE}/today")
        assert source.calls > calls


class TestCacheKey:
    def test_different_query_values_do_not_share_a_result(self):
        source = MockSalesSource(customers=CUSTOMERS)
        client, _ = make(source)
        one = client.get(f"{BASE}/top-customers?top=1").json()
        two = client.get(f"{BASE}/top-customers?top=2").json()
        assert len(one["customers"]) == 1
        assert len(two["customers"]) == 2

    def test_different_routes_do_not_share_a_result(self):
        client, _ = make(full_source())
        assert client.get(f"{BASE}/today").json() != client.get(f"{BASE}/month-to-date").json()

    def test_minimum_is_part_of_the_key(self):
        client, _ = make(MockSalesSource(orders=ORDERS))
        low = client.get(f"{BASE}/high-value-orders?minimum=100000").json()
        high = client.get(f"{BASE}/high-value-orders?minimum=200000").json()
        assert len(low["orders"]) == 2
        assert len(high["orders"]) == 1
        assert Decimal(high["orders"][0]["net_amount"]) == Decimal("250000.00")


class TestStale:
    def test_failing_refresh_serves_the_old_value(self):
        source = full_source()
        client, clock = make(source)
        good = client.get(f"{BASE}/today")
        source.fail()
        clock.now = 301
        stale = client.get(f"{BASE}/today")
        assert stale.status_code == 200
        assert stale.json() == good.json()

    def test_failing_source_without_an_old_value_is_503(self):
        source = full_source()
        source.fail()
        client, _ = make(source)
        assert client.get(f"{BASE}/today").status_code == 503

    def test_recovered_source_replaces_the_old_value(self):
        source = full_source()
        client, clock = make(source)
        client.get(f"{BASE}/today")
        source.fail()
        clock.now = 301
        client.get(f"{BASE}/today")
        source.recover()
        source.daily = []
        assert client.get(f"{BASE}/today").json() == {"totals": []}


class TestInvalidIsNotCached:
    def test_invalid_query_is_422_every_time(self):
        client, _ = make(full_source())
        assert client.get(f"{BASE}/top-customers?top=0").status_code == 422
        assert client.get(f"{BASE}/top-customers?top=0").status_code == 422
