from datetime import date
from decimal import Decimal

import httpx
import pytest
from structured_logging.request_id import request_id_var

from sami_agents.domain.entities.finding import MemberChange, Window
from sami_agents.domain.errors import DataUnavailable
from sami_agents.infrastructure.mock_data_source import MockDataSource
from sami_agents.infrastructure.settings import Settings
from sami_agents.infrastructure.synapse_data_source import SynapseDataSource

WINDOW = Window.before(date(2026, 8, 1), date(2026, 8, 31))


def source(handler) -> SynapseDataSource:
    return SynapseDataSource(Settings(synapse_url="http://synapse", _env_file=None), httpx.MockTransport(handler))


def answer(body):
    return lambda request: httpx.Response(200, json=body)


COMPARE = {"comparisons": [{"currency": "INR", "rows": [
    {"key": "A", "current": "10.00", "previous": "100.00", "volume_effect": None, "price_effect": None},
    {"key": "M", "current": "85.00", "previous": "100.00", "volume_effect": "0.00", "price_effect": "-15.00"},
]}]}


class TestRecords:
    def test_it_sends_the_type_key_field_window_and_the_users_cookie(self):
        seen = []

        def handler(request):
            seen.append(request)
            return httpx.Response(200, json={"records": [{"PurchaseOrder": "4500001207"}]})

        rows = source(handler).records("tok", "purchase_delivery", "Material", "RAW-2002", date(2026, 7, 1), date(2026, 7, 31))
        assert rows == [{"PurchaseOrder": "4500001207"}]
        request = seen[0]
        assert request.url.path == "/v1/synapse/records"
        assert dict(request.url.params) == {"type": "purchase_delivery", "key": "RAW-2002", "key_field": "Material", "start": "2026-07-01", "end": "2026-07-31"}
        assert request.headers["cookie"] == "access_token=tok"

    def test_a_type_without_a_window_sends_no_dates(self):
        seen = []

        def handler(request):
            seen.append(dict(request.url.params))
            return httpx.Response(200, json={"records": []})

        source(handler).records("tok", "production_component", "ProductionOrder", "O1", None, None)
        assert "start" not in seen[0] and "end" not in seen[0]

    def test_the_request_id_is_sent(self):
        seen = []

        def handler(request):
            seen.append(request.headers.get("x-request-id"))
            return httpx.Response(200, json={"records": []})

        token = request_id_var.set("req-4")
        try:
            source(handler).records("tok", "contract", "SoldToParty", "X", date(2026, 8, 1), date(2026, 8, 31))
        finally:
            request_id_var.reset(token)
        assert seen == ["req-4"]


class TestMemberChange:
    def test_it_asks_for_the_top_changes_of_the_dimension_and_finds_the_member(self):
        seen = []

        def handler(request):
            seen.append(request)
            return httpx.Response(200, json=COMPARE)

        change = source(handler).member_change("tok", "sales", "material", "M", WINDOW)
        assert seen[0].url.path == "/v1/synapse/metrics/sales/compare"
        assert dict(seen[0].url.params) == {"start": "2026-08-01", "end": "2026-08-31", "compare_start": "2026-07-01", "compare_end": "2026-07-31", "by": "material", "top": "50"}
        assert change == MemberChange(Decimal("85.00"), Decimal("100.00"), Decimal("-15.00"), Decimal("0.00"), Decimal("-15.00"))

    def test_a_member_without_effects_has_none(self):
        change = source(answer(COMPARE)).member_change("tok", "sales", "customer", "A", WINDOW)
        assert (change.change_percent, change.volume_effect, change.price_effect) == (Decimal("-90.00"), None, None)

    def test_a_member_that_is_not_in_the_answer_is_none(self):
        assert source(answer(COMPARE)).member_change("tok", "sales", "customer", "Z", WINDOW) is None

    def test_a_member_with_no_previous_value_has_no_percent(self):
        body = {"comparisons": [{"currency": "INR", "rows": [{"key": "N", "current": "5.00", "previous": "0.00"}]}]}
        assert source(answer(body)).member_change("tok", "sales", "customer", "N", WINDOW).change_percent is None


class TestFailures:
    @pytest.mark.parametrize("handler", [
        lambda request: httpx.Response(500),
        lambda request: httpx.Response(401),
        lambda request: httpx.Response(200, text="not json"),
    ])
    def test_a_bad_answer_is_data_unavailable(self, handler):
        with pytest.raises(DataUnavailable):
            source(handler).records("tok", "contract", "SoldToParty", "X", date(2026, 8, 1), date(2026, 8, 31))

    def test_a_connection_error_is_data_unavailable(self):
        def handler(request):
            raise httpx.ConnectError("down")

        with pytest.raises(DataUnavailable):
            source(handler).member_change("tok", "sales", "customer", "A", WINDOW)


class TestMock:
    def test_it_filters_by_the_key_field_and_records_the_calls_and_tokens(self):
        mock = MockDataSource({"contract": [{"SoldToParty": "A", "x": 1}, {"SoldToParty": "B", "x": 2}]})
        assert mock.records("tok", "contract", "SoldToParty", "A", None, None) == [{"SoldToParty": "A", "x": 1}]
        assert mock.tokens == ["tok"] and mock.calls[0][:4] == ("records", "contract", "SoldToParty", "A")

    def test_it_returns_the_given_member_change_or_none(self):
        change = MemberChange(Decimal(1), Decimal(2), Decimal(-50))
        mock = MockDataSource(changes={("sales", "material", "M"): change})
        assert mock.member_change("t", "sales", "material", "M", WINDOW) is change
        assert mock.member_change("t", "sales", "material", "Z", WINDOW) is None

    def test_it_can_fail(self):
        mock = MockDataSource()
        mock.fail()
        with pytest.raises(DataUnavailable):
            mock.records("t", "contract", "k", "v", None, None)
