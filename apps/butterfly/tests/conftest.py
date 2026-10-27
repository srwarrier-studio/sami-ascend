from datetime import date, datetime, timezone

from fastapi.testclient import TestClient

from butterfly.entrypoint.app import create_app
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo
from butterfly.infrastructure.memory.seed import build_seed

TODAY = date(2026, 10, 27)
ORDERS = build_seed(TODAY)
NOW = datetime(2026, 10, 27, 9, 15, 30, tzinfo=timezone.utc)


def make_client(orders=ORDERS) -> TestClient:
    return TestClient(create_app(InMemorySalesOrderRepo(orders), now=lambda: NOW))
