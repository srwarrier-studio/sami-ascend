import os
import sys
from datetime import date, datetime, timezone

import pytest
from fastapi.testclient import TestClient

from butterfly.entrypoint.app import create_app
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo
from butterfly.infrastructure.memory.seed import build_seed

TODAY = date(2026, 10, 27)
ORDERS = build_seed(TODAY)
NOW = datetime(2026, 10, 27, 9, 15, 30, tzinfo=timezone.utc)


def make_client(orders=ORDERS) -> TestClient:
    return TestClient(create_app(InMemorySalesOrderRepo(orders), now=lambda: NOW))


@pytest.fixture(autouse=True)
def sqlite_store(monkeypatch):
    if os.environ.get("BUTTERFLY_STORE") != "sqlite":
        return
    from butterfly.infrastructure.sqlite.driver_repo import SqliteDriverRepo
    from butterfly.infrastructure.sqlite.master_data_repo import SqliteMasterDataRepo
    from butterfly.infrastructure.sqlite.sales_order_repo import SqliteSalesOrderRepo

    replacements = {
        "InMemorySalesOrderRepo": SqliteSalesOrderRepo.from_orders,
        "InMemoryDriverRepo": SqliteDriverRepo.from_lists,
        "InMemoryMasterDataRepo": SqliteMasterDataRepo,
    }
    for module in list(sys.modules.values()):
        for name, factory in replacements.items():
            if module is not None and getattr(module, "__name__", "").startswith(("butterfly.entrypoint", "conftest", "test", "contract_helpers", "driver_data")) and hasattr(module, name):
                monkeypatch.setattr(module, name, factory)
