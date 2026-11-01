from datetime import date
from decimal import Decimal

import httpx
import pytest

from intent_api.domain.entities.figures import Window
from intent_api.domain.errors import MetricsUnavailable
from intent_api.infrastructure.settings import Settings
from intent_api.infrastructure.synapse_metric_source import SynapseMetricSource

WINDOW = Window(date(2026, 6, 1), date(2026, 6, 30), date(2026, 5, 1), date(2026, 5, 31))
MONTH = {
    "figures": [
        {
            "currency": "INR", "net_amount": "6480000.00", "order_count": 41, "previous_change_percent": "-4.20", "complete": True,
            "trend": [{"year": 2026, "month": 5, "net_amount": "6764000.00"}, {"year": 2026, "month": 6, "net_amount": "6480000.00"}],
        }
    ]
}


def row(key, name, current, previous):
    return {"key": key, "name": name, "current": current, "previous": previous, "change": "0", "share_of_change_percent": None}


COMPARE = {
    "comparisons": [
        {
            "currency": "USD", "current": "500.00", "previous": "400.00", "change": "100.00", "change_percent": "25.00",
            "rows": [row("C1", "Alder Imports", "300.00", "100.00"), row("other", "Other", "200.00", "300.00")],
        }
    ]
}


def source_with(handler, **settings) -> SynapseMetricSource:
    return SynapseMetricSource(Settings(_env_file=None, **settings), httpx.MockTransport(handler))


def answering(body, status=200):
    return lambda request: httpx.Response(status, json=body)


class TestMonth:
    def test_asks_for_the_month_and_the_trend_with_the_cookie_forwarded(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["url"] = request.url
            seen["cookie"] = request.headers["cookie"]
            return httpx.Response(200, json=MONTH)

        source_with(handler).month("tok", "sales", date(2026, 6, 1), 6)
        assert seen["url"].path == "/v1/synapse/metrics/sales/month"
        assert dict(seen["url"].params) == {"month": "2026-06", "trend": "6"}
        assert "tok" in seen["cookie"]

    def test_reads_the_figure_per_currency(self):
        [figure] = source_with(answering(MONTH)).month("tok", "sales", date(2026, 6, 1), 6)
        assert (figure.currency, figure.amount, figure.change_percent, figure.complete) == ("INR", Decimal("6480000.00"), Decimal("-4.20"), True)
        assert [(point.month, point.amount) for point in figure.trend] == [(5, Decimal("6764000.00")), (6, Decimal("6480000.00"))]

    def test_no_figures_is_an_empty_list(self):
        assert source_with(answering({"figures": []})).month("tok", "sales", date(2026, 6, 1), 6) == []

    def test_the_base_address_comes_from_settings(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["host"] = request.url.host
            return httpx.Response(200, json=MONTH)

        source_with(handler, synapse_url="http://synapse.internal:9000").month("tok", "sales", date(2026, 6, 1), 6)
        assert seen["host"] == "synapse.internal"


class TestCompare:
    def test_asks_for_both_windows_and_the_dimension(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["params"] = dict(request.url.params)
            seen["path"] = request.url.path
            return httpx.Response(200, json=COMPARE)

        source_with(handler).compare("tok", "sales", WINDOW, "customer", 50)
        assert seen["path"] == "/v1/synapse/metrics/sales/compare"
        assert seen["params"] == {
            "start": "2026-06-01", "end": "2026-06-30", "compare_start": "2026-05-01", "compare_end": "2026-05-31", "top": "50", "by": "customer",
        }

    def test_no_dimension_means_no_by(self):
        seen = {}

        def handler(request: httpx.Request) -> httpx.Response:
            seen["params"] = dict(request.url.params)
            return httpx.Response(200, json={"comparisons": []})

        source_with(handler).compare("tok", "sales", WINDOW, None, 10)
        assert "by" not in seen["params"]

    def test_the_other_row_is_left_out_and_the_comparison_is_marked_truncated(self):
        [comparison] = source_with(answering(COMPARE)).compare("tok", "sales", WINDOW, "customer", 50)
        assert [(row.key, row.current) for row in comparison.rows] == [("C1", Decimal("300.00"))]
        assert (comparison.currency, comparison.change_percent, comparison.truncated) == ("USD", Decimal("25.00"), True)

    def test_a_comparison_with_every_row_is_not_truncated(self):
        body = {"comparisons": [{**COMPARE["comparisons"][0], "rows": [row("C1", "Alder Imports", "500.00", "400.00")]}]}
        [comparison] = source_with(answering(body)).compare("tok", "sales", WINDOW, "customer", 50)
        assert comparison.truncated is False

    def test_a_comparison_without_rows_has_none(self):
        body = {"comparisons": [{**COMPARE["comparisons"][0], "rows": None}]}
        [comparison] = source_with(answering(body)).compare("tok", "sales", WINDOW, None, 10)
        assert (comparison.rows, comparison.truncated) == ((), False)


class TestFailures:
    @pytest.mark.parametrize("call", ["month", "compare"])
    def test_a_connection_error(self, call):
        def handler(request):
            raise httpx.ConnectError("refused")

        with pytest.raises(MetricsUnavailable):
            fetch(source_with(handler), call)

    @pytest.mark.parametrize("call", ["month", "compare"])
    @pytest.mark.parametrize("status", [401, 404, 500])
    def test_a_status_other_than_200(self, call, status):
        with pytest.raises(MetricsUnavailable, match=str(status)):
            fetch(source_with(answering({}, status)), call)

    @pytest.mark.parametrize("call", ["month", "compare"])
    def test_a_body_that_is_not_json(self, call):
        with pytest.raises(MetricsUnavailable, match="unreadable"):
            fetch(source_with(lambda request: httpx.Response(200, content=b"<html>")), call)

    @pytest.mark.parametrize("call", ["month", "compare"])
    def test_a_body_with_the_wrong_shape(self, call):
        with pytest.raises(MetricsUnavailable, match="unreadable"):
            fetch(source_with(answering({"unexpected": 1})), call)

    def test_a_number_that_is_not_a_number(self):
        body = {"figures": [{**MONTH["figures"][0], "net_amount": "abc"}]}
        with pytest.raises(MetricsUnavailable):
            source_with(answering(body)).month("tok", "sales", date(2026, 6, 1), 6)


def fetch(source, call):
    if call == "month":
        return source.month("tok", "sales", date(2026, 6, 1), 6)
    return source.compare("tok", "sales", WINDOW, "customer", 50)


class TestACompany:
    def test_the_company_is_sent_with_every_read(self):
        seen = []

        def handler(request):
            seen.append(dict(request.url.params))
            return httpx.Response(200, json=MONTH)

        scoped = source_with(handler).for_company("sabinsa")
        scoped.month("tok", "sales", date(2026, 6, 1), 6)
        assert seen[0]["company"] == "sabinsa"

    def test_nothing_is_added_without_a_company(self):
        seen = []

        def handler(request):
            seen.append(dict(request.url.params))
            return httpx.Response(200, json=MONTH)

        source_with(handler).month("tok", "sales", date(2026, 6, 1), 6)
        assert "company" not in seen[0]

    def test_403_for_a_company_is_company_not_allowed(self):
        from intent_api.domain.errors import CompanyNotAllowed

        with pytest.raises(CompanyNotAllowed):
            source_with(lambda request: httpx.Response(403)).for_company("organica").month("tok", "sales", date(2026, 6, 1), 6)
