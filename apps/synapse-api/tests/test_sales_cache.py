import logging
import threading
import time

import pytest

from synapse_api.application.sales_cache import SalesCache
from synapse_api.domain.errors import SapUnavailable
from synapse_api.infrastructure.settings import Settings


class Clock:
    def __init__(self):
        self.now = 0.0

    def __call__(self) -> float:
        return self.now


class Loader:
    def __init__(self, value="v1"):
        self.value = value
        self.calls = 0
        self.failing = False

    def __call__(self):
        self.calls += 1
        if self.failing:
            raise SapUnavailable()
        return self.value


def make():
    clock = Clock()
    return SalesCache(300, clock), clock, Loader()


class TestFreshValue:
    def test_second_read_inside_ttl_does_not_load(self):
        cache, clock, load = make()
        cache.get("today", load)
        clock.now = 299
        assert cache.get("today", load) == "v1"
        assert load.calls == 1

    def test_read_after_ttl_loads_again(self):
        cache, clock, load = make()
        cache.get("today", load)
        clock.now = 300
        load.value = "v2"
        assert cache.get("today", load) == "v2"
        assert load.calls == 2

    def test_different_keys_do_not_share_values(self):
        cache, _, load = make()
        other = Loader("other")
        cache.get(("top", 5), load)
        assert cache.get(("top", 10), other) == "other"


class TestSapFailure:
    def test_failed_refresh_returns_old_value_and_logs(self, caplog):
        cache, clock, load = make()
        cache.get(("today", "2026"), load)
        clock.now = 400
        load.failing = True
        with caplog.at_level(logging.WARNING):
            assert cache.get(("today", "2026"), load) == "v1"
        assert "stale" in caplog.text

    def test_failed_refresh_is_retried_on_next_read(self):
        cache, clock, load = make()
        cache.get("today", load)
        clock.now = 400
        load.failing = True
        cache.get("today", load)
        load.failing = False
        load.value = "v2"
        assert cache.get("today", load) == "v2"

    def test_failed_first_read_raises(self):
        cache, _, load = make()
        load.failing = True
        with pytest.raises(SapUnavailable):
            cache.get("today", load)


class TestSeveralThreads:
    def test_simultaneous_first_reads_load_once(self):
        cache = SalesCache(300)
        calls = []

        def slow():
            calls.append(1)
            time.sleep(0.05)
            return "v1"

        threads = [threading.Thread(target=cache.get, args=("k", slow)) for _ in range(5)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert len(calls) == 1


class TestSettings:
    def test_default_is_five_minutes(self, monkeypatch):
        monkeypatch.delenv("CACHE_SECONDS", raising=False)
        assert Settings().cache_seconds == 300

    def test_reads_cache_seconds_from_environment(self, monkeypatch):
        monkeypatch.setenv("CACHE_SECONDS", "60")
        assert Settings().cache_seconds == 60

    def test_jwt_secret_and_frontend_url_have_defaults(self, monkeypatch):
        monkeypatch.delenv("JWT_SECRET", raising=False)
        monkeypatch.delenv("FRONTEND_URL", raising=False)
        settings = Settings()
        assert settings.jwt_secret == ""
        assert settings.frontend_url == "http://localhost:5173"
