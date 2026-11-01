from datetime import date
from decimal import Decimal

import httpx
import pytest
from structured_logging.request_id import request_id_var

from intent_api.domain.analysis.finding import MemberChange, Window
from intent_api.domain.analysis.measure import Comparison, DimensionInfo, MetricInfo, MoverRow, TrendPoint
from intent_api.domain.errors import DataUnavailable
from intent_api.infrastructure.mock_data_source import MockDataSource
from intent_api.infrastructure.settings import Settings
from intent_api.infrastructure.synapse_data_source import SynapseDataSource

WINDOW = Window.before(date(2026, 8, 1), date(2026, 8, 31))


def source(handler) -> SynapseDataSource:
    return SynapseDataSource(Settings(synapse_url="http://synapse", _env_file=None), httpx.MockTransport(handler))


def answer(body):
    return lambda request: httpx.Response(200, json=body)


def compare_row(key, current, previous, volume=None, price=None, name=None, share="100.00"):
    change = f"{float(current) - float(previous):.2f}"
    return {"key": key, "name": name or f"Name {key}", "current": current, "previous": previous, "change": change,
            "share_of_change_percent": share, "unit": "KG" if volume is not None else None, "volume_effect": volume, "price_effect": price}


COMPARE = {"comparisons": [{"currency": "INR", "current": "98.00", "previous": "200.00", "change": "-102.00", "change_percent": "-51.00", "rows": [
    compare_row("A", "10.00", "100.00"),
    compare_row("M", "85.00", "100.00", "0.00", "-15.00"),
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
        body = {"comparisons": [{"currency": "INR", "current": "5.00", "previous": "0.00", "change": "5.00", "change_percent": None, "rows": [compare_row("N", "5.00", "0.00")]}]}
        assert source(answer(body)).member_change("tok", "sales", "customer", "N", WINDOW).change_percent is None


class TestMetrics:
    def test_the_registered_metrics_and_their_dimensions(self):
        body = {"metrics": [{"name": "sales", "label": "Sales", "dimensions": [{"name": "customer", "splits_volume_and_price": False}, {"name": "material", "splits_volume_and_price": True}]}]}
        seen = []

        def handler(request):
            seen.append(request)
            return httpx.Response(200, json=body)

        assert source(handler).metrics("tok") == [MetricInfo("sales", "Sales", (DimensionInfo("customer", False), DimensionInfo("material", True)))]
        assert seen[0].url.path == "/v1/synapse/metrics" and seen[0].headers["cookie"] == "access_token=tok"


class TestCompare:
    def test_totals_and_rows_with_their_effects(self):
        seen = []

        def handler(request):
            seen.append(request)
            return httpx.Response(200, json=COMPARE)

        [comparison] = source(handler).compare("tok", "sales", WINDOW, "material", 10)
        assert (comparison.currency, comparison.current, comparison.previous, comparison.change, comparison.change_percent) == ("INR", Decimal("98.00"), Decimal("200.00"), Decimal("-102.00"), Decimal("-51.00"))
        assert comparison.rows[1] == MoverRow("M", "Name M", Decimal("85.00"), Decimal("100.00"), Decimal("-15.00"), Decimal("100.00"), "KG", Decimal("0.00"), Decimal("-15.00"))
        assert dict(seen[0].url.params)["by"] == "material" and dict(seen[0].url.params)["top"] == "10"

    def test_without_a_dimension_there_are_no_rows_and_no_by(self):
        seen = []
        body = {"comparisons": [{"currency": "INR", "current": "1.00", "previous": "2.00", "change": "-1.00", "change_percent": "-50.00", "rows": None}]}

        def handler(request):
            seen.append(request)
            return httpx.Response(200, json=body)

        [comparison] = source(handler).compare("tok", "sales", WINDOW, None, 10)
        assert comparison.rows is None and "by" not in dict(seen[0].url.params)

    def test_the_comparison_uses_the_given_previous_period(self):
        seen = []

        def handler(request):
            seen.append(dict(request.url.params))
            return httpx.Response(200, json={"comparisons": []})

        source(handler).compare("tok", "sales", Window(date(2026, 9, 1), date(2026, 9, 30), date(2026, 8, 1), date(2026, 8, 31)), None, 10)
        assert seen[0]["compare_start"] == "2026-08-01" and seen[0]["compare_end"] == "2026-08-31"


class TestTrend:
    def test_the_months_of_the_first_currency_oldest_first(self):
        body = {"figures": [{"currency": "INR", "trend": [{"year": 2026, "month": 7, "net_amount": "100.00"}, {"year": 2026, "month": 8, "net_amount": "80.00"}]}]}
        seen = []

        def handler(request):
            seen.append(dict(request.url.params))
            return httpx.Response(200, json=body)

        assert source(handler).trend("tok", "sales", date(2026, 8, 1), 2) == [TrendPoint("2026-07", Decimal("100.00")), TrendPoint("2026-08", Decimal("80.00"))]
        assert seen[0] == {"month": "2026-08", "trend": "2"}

    def test_no_data_is_an_empty_trend(self):
        assert source(answer({"figures": []})).trend("tok", "sales", date(2026, 8, 1), 6) == []


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

    def test_it_serves_the_new_reads_and_records_them(self):
        info = MetricInfo("sales", "Sales", ())
        comparison = Comparison("INR", Decimal(1), Decimal(2), Decimal(-1), Decimal("-50.00"))
        point = TrendPoint("2026-08", Decimal(5))
        mock = MockDataSource(infos=[info], comparisons={("sales", "customer"): [comparison]}, trends={"sales": [point]})
        assert mock.metrics("t") == [info]
        assert mock.compare("t", "sales", WINDOW, "customer", 10) == [comparison]
        assert mock.compare("t", "sales", WINDOW, "material", 10) == []
        assert mock.trend("t", "sales", date(2026, 8, 1), 6) == [point]
        assert [c[0] for c in mock.calls] == ["metrics", "compare", "compare", "trend"]

    def test_it_can_fail(self):
        mock = MockDataSource()
        mock.fail()
        with pytest.raises(DataUnavailable):
            mock.records("t", "contract", "k", "v", None, None)


class TestCompanyScope:
    def urls(self, company):
        seen = []

        def handler(request):
            seen.append(str(request.url))
            return httpx.Response(200, json={"comparisons": [], "metrics": [], "records": [], "figures": []})

        scoped = source(handler).for_company(company)
        scoped.compare("tok", "sales", Window(date(2026, 8, 1), date(2026, 8, 31), date(2026, 7, 1), date(2026, 7, 31)), None, 10)
        scoped.metrics("tok")
        scoped.records("tok", "contract", "SoldToParty", "X", None, None)
        scoped.trend("tok", "sales", date(2026, 8, 1), 6)
        return seen

    def test_every_read_carries_the_company(self):
        assert all("company=sabinsa" in url for url in self.urls("sabinsa"))

    def test_without_a_company_nothing_is_added(self):
        assert not any("company=" in url for url in self.urls(None))

    def test_the_scoped_source_is_a_new_one_and_the_original_stays_unscoped(self):
        original = source(lambda request: httpx.Response(200, json={}))
        assert original.for_company("organica") is not original and original.company is None

    def test_the_mock_records_the_company_it_was_scoped_to(self):
        mock = MockDataSource()
        assert mock.for_company("all") is mock and mock.companies == ["all"]


class TestACompanyTheUserDoesNotHave:
    def test_403_with_a_company_is_company_not_allowed(self):
        from intent_api.domain.errors import CompanyNotAllowed

        with pytest.raises(CompanyNotAllowed):
            source(lambda request: httpx.Response(403, json={"code": "COMPANY_NOT_ALLOWED"})).for_company("organica").metrics("tok")

    def test_403_without_a_company_is_just_unavailable(self):
        with pytest.raises(DataUnavailable):
            source(lambda request: httpx.Response(403)).metrics("tok")
