from workspace_api.infrastructure.settings import Settings


class TestWorstCaseDefaults:
    def test_defaults_assume_sap_takes_one_write_at_a_time(self, monkeypatch):
        for name in ("SAP_WRITE_LIMIT", "SAP_WRITE_WAIT_SECONDS", "ORDER_WORKERS", "ORDER_MAX_ATTEMPTS", "ORDER_DB"):
            monkeypatch.delenv(name, raising=False)
        s = Settings()
        assert (s.sap_write_limit, s.sap_write_wait_seconds, s.order_workers, s.order_max_attempts) == (1, 2.0, 1, 8)
        assert s.order_db.endswith("orders.db")

    def test_every_limit_can_be_raised_from_the_environment(self, monkeypatch):
        monkeypatch.setenv("SAP_WRITE_LIMIT", "6")
        monkeypatch.setenv("SAP_WRITE_WAIT_SECONDS", "0.5")
        monkeypatch.setenv("ORDER_WORKERS", "0")
        monkeypatch.setenv("ORDER_MAX_ATTEMPTS", "3")
        monkeypatch.setenv("ORDER_DB", "/tmp/x.db")
        s = Settings()
        assert (s.sap_write_limit, s.sap_write_wait_seconds, s.order_workers, s.order_max_attempts, s.order_db) == (6, 0.5, 0, 3, "/tmp/x.db")
