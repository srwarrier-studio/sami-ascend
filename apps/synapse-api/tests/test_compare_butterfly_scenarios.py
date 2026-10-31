from datetime import date
from decimal import Decimal

import httpx
import pytest

pytest.importorskip("butterfly")
from fastapi.testclient import TestClient

from butterfly.entrypoint.app import build_default_app
from synapse_api.application.compare_metric import CompareMetric
from synapse_api.infrastructure.odata_reader import ODataReader
from synapse_api.infrastructure.registry_loader import load_registry
from synapse_api.infrastructure.registry_metric_source import RegistryMetricSource
from synapse_api.infrastructure.settings import REGISTRY_PATH

TODAY = date(2026, 10, 31)
REGISTRY = load_registry(REGISTRY_PATH)
JULY = (date(2026, 7, 1), date(2026, 7, 31))
AUGUST = (date(2026, 8, 1), date(2026, 8, 31))
ROOT = "http://testserver/sap/opu/odata4/sap/zui_sales_o4/srvd_a2x/sap/zsales/0001/"


class InProcess(httpx.BaseTransport):
    def __init__(self, scenario: str):
        self.butterfly = TestClient(build_default_app(TODAY, "story", scenario))

    def handle_request(self, request: httpx.Request) -> httpx.Response:
        answer = self.butterfly.get(str(request.url))
        return httpx.Response(answer.status_code, json=answer.json())


def compare(scenario: str, by: str | None, current=AUGUST, previous=JULY, top: int = 10):
    source = RegistryMetricSource({"sales": ODataReader(ROOT, 10, InProcess(scenario))})
    [result] = CompareMetric(source, REGISTRY).execute("sales", *current, *previous, by, top)
    return result


class TestAugustContract:
    def test_august_is_14_percent_below_july(self):
        assert Decimal("-16") <= compare("august-contract", None).change_percent <= Decimal("-13")

    def test_acme_is_about_80_percent_of_the_change_and_the_rows_add_up(self):
        result = compare("august-contract", "customer")
        assert result.rows[0].key == "0000100001"
        assert 70 <= result.rows[0].share_of_change_percent <= 90
        assert sum(r.change for r in result.rows) == result.change


class TestPriceCut:
    def test_steel_rod_shows_a_price_effect_and_a_small_volume_effect(self):
        rod = next(r for r in compare("price-cut", "material").rows if r.key == "RM-1001")
        assert Decimal("-16") <= rod.price_effect / rod.previous * 100 <= Decimal("-13")
        assert abs(rod.volume_effect) / rod.previous < Decimal("0.08")

    def test_other_materials_have_almost_no_price_effect(self):
        others = [r for r in compare("price-cut", "material").rows if r.key != "RM-1001"]
        assert others
        assert all(abs(r.price_effect) / r.previous < Decimal("0.01") for r in others)


class TestCustomerLost:
    def test_eastern_is_the_first_row_and_has_nothing_after_its_last_order(self):
        result = compare("customer-lost", "customer", current=(date(2026, 8, 15), date(2026, 8, 31)))
        assert result.rows[0].key == "0000100005"
        assert result.rows[0].current == Decimal(0)
