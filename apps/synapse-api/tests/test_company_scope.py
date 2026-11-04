from datetime import date
from decimal import Decimal

import httpx
import pytest
from fastapi.testclient import TestClient
from test_routes_totals import SECRET, TODAY, token_with
from token_verification.fastapi_deps import ACCESS_TOKEN_COOKIE

from butterfly.entrypoint.app import build_default_app
from synapse_api.application.compare_metric import CompareMetric
from synapse_api.entrypoint.app import create_app
from synapse_api.infrastructure.butterfly_sales_source import ButterflySalesSource
from synapse_api.infrastructure.mock_metric_source import MockMetricSource
from synapse_api.infrastructure.mock_record_source import MockRecordSource
from synapse_api.infrastructure.mock_sales_source import MockSalesSource
from synapse_api.infrastructure.odata_reader import ODataReader
from synapse_api.infrastructure.registry_loader import load_registry
from synapse_api.infrastructure.registry_metric_source import RegistryMetricSource
from synapse_api.infrastructure.registry_record_source import RegistryRecordSource
from synapse_api.infrastructure.settings import REGISTRY_PATH, Settings

pytest.importorskip("butterfly")

REGISTRY = load_registry(REGISTRY_PATH)
BASE = "/v1/synapse"
SALES_ROOT = "http://testserver/sap/opu/odata4/sap/zui_sales_o4/srvd_a2x/sap/zsales/0001/"
AUGUST, JULY = (date(2026, 8, 1), date(2026, 8, 31)), (date(2026, 7, 1), date(2026, 7, 31))


def client(companies: list[str] | None) -> TestClient:
    app = create_app(MockSalesSource(), Settings(jwt_secret=SECRET, _env_file=None), lambda: TODAY, metrics=MockMetricSource(), records=MockRecordSource())
    http = TestClient(app)
    http.cookies.set(ACCESS_TOKEN_COOKIE, token_with(["management"], companies))
    return http


class TestWhoMayAsk:
    def test_a_company_of_the_user_is_allowed(self):
        assert client(["sabinsa"]).get(f"{BASE}/sales/today?company=sabinsa").status_code == 200

    def test_another_company_is_403(self):
        response = client(["sabinsa"]).get(f"{BASE}/sales/today?company=organica")
        assert (response.status_code, response.json()) == (403, {"code": "COMPANY_NOT_ALLOWED"})

    def test_all_means_every_company_of_the_user_and_is_the_default(self):
        assert client(["sabinsa"]).get(f"{BASE}/sales/today?company=all").json() == client(["sabinsa"]).get(f"{BASE}/sales/today").json()

    def test_a_user_with_no_company_is_403_even_for_all(self):
        assert client([]).get(f"{BASE}/sales/today").status_code == 403

    def test_an_unknown_company_is_422(self):
        response = client(["sabinsa"]).get(f"{BASE}/sales/today?company=acme")
        assert (response.status_code, response.json()["code"]) == (422, "INVALID_QUERY")

    @pytest.mark.parametrize("path", [
        "sales/top-customers", "sales/month-on-month", "catalog/sales-today/data",
        "metrics/sales/compare?start=2026-08-01&end=2026-08-31&compare_start=2026-07-01&compare_end=2026-07-31",
        "metrics/sales/month?month=2026-08", "records?type=contract&key=X",
    ])
    def test_every_route_checks_the_company(self, path):
        separator = "&" if "?" in path else "?"
        assert client(["sabinsa"]).get(f"{BASE}/{path}{separator}company=organica").status_code == 403


class Recorder(httpx.BaseTransport):
    def __init__(self):
        self.urls: list[str] = []

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        self.urls.append(str(request.url))
        return httpx.Response(200, json={"value": []})


class TestTheFilterSentToButterfly:
    def filters(self, recorder: Recorder) -> list[str]:
        return [url.split("$filter=")[1].split("&")[0] for url in recorder.urls]

    def test_the_sales_source_names_the_companies_in_every_read(self):
        recorder = Recorder()
        source = ButterflySalesSource(Settings(sap_base_url="http://sap/root/", _env_file=None), recorder).for_companies(("INA1", "INA3"))
        source.daily_sales(date(2026, 8, 1), date(2026, 8, 31))
        source.customer_sales(date(2026, 8, 1), date(2026, 8, 31))
        source.order_statuses(date(2026, 8, 1), date(2026, 8, 31))
        source.high_value_orders(Decimal(1), 5)
        assert all("(CompanyCode%20eq%20'INA1'%20or%20CompanyCode%20eq%20'INA3')" in f for f in self.filters(recorder))

    def test_the_metric_source_uses_the_company_field_of_the_registry(self):
        recorder = Recorder()
        source = RegistryMetricSource({"sales": ODataReader("http://sap/root/", 5, recorder)}).for_companies(("INA2",))
        source.rows(REGISTRY.metrics["sales"], "day", date(2026, 8, 1), date(2026, 8, 31))
        assert "(CompanyCode%20eq%20'INA2')" in self.filters(recorder)[0]
        assert "$orderby=OrderDate,Currency,CompanyCode" in recorder.urls[0]

    def test_the_record_source_too(self):
        recorder = Recorder()
        source = RegistryRecordSource({"drivers": ODataReader("http://sap/root/", 5, recorder)}).for_companies(("INA1", "INA2"))
        source.rows(REGISTRY.records["contract"], "SoldToParty", "0000100001", date(2026, 8, 1))
        assert "(CompanyCode%20eq%20'INA1'%20or%20CompanyCode%20eq%20'INA2')" in self.filters(recorder)[0]

    def test_every_summary_order_in_the_registry_ends_with_the_company(self):
        for metric in REGISTRY.metrics.values():
            assert metric.company == "CompanyCode"
            assert all(d.order.endswith("CompanyCode") for d in metric.dimensions.values())


class InProcess(httpx.BaseTransport):
    def __init__(self):
        self.butterfly = TestClient(build_default_app(date(2026, 10, 31), "story", "august-contract"))

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        answer = self.butterfly.get(str(request.url))
        return httpx.Response(answer.status_code, json=answer.json())


class TestAgainstTheGroupData:
    source = RegistryMetricSource({"sales": ODataReader(SALES_ROOT, 10, InProcess())})

    def total(self, companies: tuple[str, ...], currency: str) -> Decimal:
        rows = self.source.for_companies(companies).rows(REGISTRY.metrics["sales"], "day", *AUGUST)
        return sum((r.amount for r in rows if r.currency == currency), Decimal(0))

    @pytest.mark.parametrize("currency", ["INR"])
    def test_all_is_the_three_companies_added_per_currency(self, currency):
        parts = sum(self.total((code,), currency) for code in ("INA1", "INA2", "INA3"))
        assert self.total(("INA1", "INA2", "INA3"), currency) == parts > 0

    def test_a_single_company_only_has_its_own_customers(self):
        rows = self.source.for_companies(("INA3",)).rows(REGISTRY.metrics["sales"], "customer", *AUGUST)
        assert rows and {r.key[:7] for r in rows} == {"0000120"}


class Scopes(MockSalesSource):
    def __init__(self):
        super().__init__()
        self.asked: list[tuple[str, ...]] = []

    def for_companies(self, companies):
        self.asked.append(companies)
        return self


class TestTheCacheKeepsCompaniesApart:
    def ask(self, source: Scopes, *queries: str):
        app = create_app(source, Settings(jwt_secret=SECRET, _env_file=None), lambda: TODAY)
        http = TestClient(app)
        http.cookies.set(ACCESS_TOKEN_COOKIE, token_with(["management"]))
        for query in queries:
            http.get(f"{BASE}/sales/today{query}")

    def test_the_same_scope_is_read_once(self):
        source = Scopes()
        self.ask(source, "?company=sabinsa", "?company=sabinsa")
        assert source.asked == [("INA1",)]

    def test_another_scope_is_read_again_and_all_is_its_own_entry(self):
        source = Scopes()
        self.ask(source, "?company=sabinsa", "?company=organica", "")
        assert source.asked == [("INA1",), ("INA3",), ("INA1", "INA2", "INA3")]
