from datetime import date, datetime, timedelta, timezone

import httpx
import pytest

pytest.importorskip("butterfly")
from fastapi.testclient import TestClient
from test_order_queue_routes import REQUESTS, URL, token
from test_routes_access import SECRET, VALID_BODY
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from butterfly.entrypoint.app import build_default_app
from butterfly.infrastructure.api.odata import ROOT
from workspace_api.application.order_worker import OrderWorker
from workspace_api.application.throttled_gateway import ThrottledGateway
from workspace_api.domain.entities.order_request import POSTED, QUEUED
from workspace_api.entrypoint.app import create_app
from workspace_api.infrastructure.butterfly_sales_order_gateway import ButterflySalesOrderGateway
from workspace_api.infrastructure.settings import Settings
from workspace_api.infrastructure.sqlite_order_request_store import SqliteOrderRequestStore




class FlakyButterfly(httpx.BaseTransport):
    def __init__(self, refusals: int):
        self.butterfly = TestClient(build_default_app(date(2026, 10, 31), "small"))
        self.refusals = refusals
        self.posts = 0

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        if request.method == "POST":
            self.posts += 1
            if self.posts <= self.refusals:
                return httpx.Response(503)
        answer = self.butterfly.request(request.method, str(request.url), content=request.content, headers=dict(request.headers))
        return httpx.Response(answer.status_code, content=answer.content, headers={"content-type": "application/json"})

    def orders_in_butterfly(self) -> int:
        return self.butterfly.get(f"{ROOT}SalesOrder?$count=true&$top=1").json()["@odata.count"]


def test_an_order_refused_three_times_is_posted_once_when_sap_recovers():
    transport = FlakyButterfly(refusals=3)
    settings = Settings(jwt_secret=SECRET, sap_base_url=f"http://testserver{ROOT}")
    gateway = ThrottledGateway(ButterflySalesOrderGateway(settings, transport), 1, 0.05)
    store = SqliteOrderRequestStore(":memory:")
    now = [datetime.now(timezone.utc)]
    worker = OrderWorker(store, gateway, 8, lambda: now[0])
    client = TestClient(create_app(gateway, settings, store))
    client.cookies.set(ACCESS_TOKEN_COOKIE, token())
    before = transport.orders_in_butterfly()

    accepted = client.post(URL, json=VALID_BODY)
    assert accepted.status_code == 202 and accepted.json()["status"] == QUEUED
    request_id = accepted.json()["id"]

    now[0] = datetime.now(timezone.utc) + timedelta(seconds=1)
    worker.run_once()
    assert client.get(f"{REQUESTS}/{request_id}").json()["attempts"] == 1
    assert worker.run_once() is False
    now[0] += timedelta(seconds=30)
    worker.run_once()
    assert transport.orders_in_butterfly() == before and client.get(f"{REQUESTS}/{request_id}").json()["status"] == QUEUED
    now[0] += timedelta(seconds=60)
    worker.run_once()

    done = client.get(f"{REQUESTS}/{request_id}").json()
    assert done["status"] == POSTED and done["sales_order"] == f"{12031:010d}"
    assert transport.orders_in_butterfly() == before + 1
    assert client.get(f"{REQUESTS}?open=true").json()["requests"] == []
