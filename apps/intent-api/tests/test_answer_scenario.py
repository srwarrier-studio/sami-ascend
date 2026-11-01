from datetime import date
from decimal import Decimal

import pytest

from intent_api.application.answer_scenario import AnswerScenario
from intent_api.application.read_period import ReadPeriod
from intent_api.domain.entities.answer import AnswerRule
from intent_api.domain.entities.figures import Comparison, MonthFigure, Row, TrendPoint
from intent_api.domain.errors import MetricsUnavailable
from tests.fakes import FakeMetricSource

TODAY = date(2026, 11, 15)
JUNE = ReadPeriod().execute("in june", TODAY)
THIS_MONTH = ReadPeriod().execute("this month", TODAY)
LAST_YEAR = ReadPeriod().execute("last year", TODAY)


def money(value) -> Decimal:
    return Decimal(str(value))


def comparison(currency="INR", current=6480000, previous=6764000, rows=(), truncated=False) -> Comparison:
    change = money(current) - money(previous)
    percent = None if not previous else (change / money(previous) * 100).quantize(Decimal("0.01"))
    return Comparison(currency, money(current), money(previous), change, percent, tuple(rows), truncated)


def rows(*pairs) -> list[Row]:
    return [Row(f"K{index}", name, money(current), money(0)) for index, (name, current) in enumerate(pairs, start=1)]


def figure(currency="INR", points=((5, 6764000), (6, 6480000))) -> MonthFigure:
    return MonthFigure(currency, money(points[-1][1]), None, True, tuple(TrendPoint(2026, month, money(amount)) for month, amount in points))


def rule(response, **fields) -> AnswerRule:
    return AnswerRule(f"sales_{response}", response, "sales", **fields)


def answer(source, response, period=JUNE, **fields):
    return AnswerScenario(source).execute(rule(response, **fields), period, "tok")


def lines(result) -> list[str]:
    return result.blocks[0].data["lines"]


class TestValue:
    def test_a_sentence_with_the_figure_and_no_chart(self):
        result = answer(FakeMetricSource(comparisons=[comparison()]), "value")
        assert [block.type for block in result.blocks] == ["text"]
        assert lines(result) == ["Sales for June 2026 were INR 6,480,000."]

    def test_a_month_still_running_says_so_far(self):
        result = answer(FakeMetricSource(comparisons=[comparison()]), "value", THIS_MONTH)
        assert lines(result) == ["Sales so far in November 2026 were INR 6,480,000."]

    def test_one_sentence_per_currency(self):
        source = FakeMetricSource(comparisons=[comparison("INR", 100), comparison("USD", 50)])
        assert lines(answer(source, "value")) == ["Sales for June 2026 were INR 100.", "Sales for June 2026 were USD 50."]

    def test_a_year_is_read_over_the_whole_year(self):
        source = FakeMetricSource(comparisons=[comparison()])
        result = answer(source, "value", LAST_YEAR)
        window = source.calls[0][3]
        assert (window.start, window.end) == (date(2025, 1, 1), date(2025, 12, 31))
        assert lines(result) == ["Sales for 2025 were INR 6,480,000."]

    def test_no_data_says_so_with_no_chart(self):
        result = answer(FakeMetricSource(), "value")
        assert [block.type for block in result.blocks] == ["text"]
        assert lines(result) == ["No sales were recorded in June 2026."]

    def test_the_cookie_and_the_metric_are_passed_on(self):
        source = FakeMetricSource(comparisons=[comparison()])
        AnswerScenario(source).execute(AnswerRule("purchases_value", "value", "purchases"), JUNE, "secret")
        assert source.calls[0][:3] == ("compare", "secret", "purchases")


class TestCompare:
    def test_both_figures_and_the_change_with_no_chart(self):
        result = answer(FakeMetricSource(comparisons=[comparison()]), "compare", against="previous")
        assert [block.type for block in result.blocks] == ["text"]
        assert lines(result) == ["Sales for June 2026 were INR 6,480,000, down 4.2% from May 2026 (INR 6,764,000)."]

    def test_against_the_same_month_last_year(self):
        source = FakeMetricSource(comparisons=[comparison(previous=5000000)])
        result = answer(source, "compare", against="last_year")
        window = source.calls[0][3]
        assert (window.compare_start, window.compare_end) == (date(2025, 6, 1), date(2025, 6, 30))
        assert lines(result) == ["Sales for June 2026 were INR 6,480,000, up 29.6% from June 2025 (INR 5,000,000)."]

    def test_a_running_month_is_compared_with_the_same_days_before(self):
        source = FakeMetricSource(comparisons=[comparison(current=100, previous=80)])
        result = answer(source, "compare", THIS_MONTH, against="previous")
        window = source.calls[0][3]
        assert (window.start, window.end) == (date(2026, 11, 1), date(2026, 11, 15))
        assert (window.compare_start, window.compare_end) == (date(2026, 10, 1), date(2026, 10, 15))
        assert lines(result)[0].startswith("Sales so far in November 2026 were INR 100, up 25.0% from October 2026")

    def test_a_year_is_compared_with_the_year_before(self):
        source = FakeMetricSource(comparisons=[comparison(current=200, previous=100)])
        result = answer(source, "compare", LAST_YEAR, against="last_year")
        assert lines(result) == ["Sales for 2025 were INR 200, up 100.0% from 2024 (INR 100)."]

    def test_nothing_before_is_up_from_nothing(self):
        result = answer(FakeMetricSource(comparisons=[comparison(current=100, previous=0)]), "compare", against="previous")
        assert lines(result) == ["Sales for June 2026 were INR 100, up from nothing in May 2026."]

    def test_no_change(self):
        result = answer(FakeMetricSource(comparisons=[comparison(current=100, previous=100)]), "compare", against="previous")
        assert lines(result) == ["Sales for June 2026 were INR 100, unchanged from May 2026 (INR 100)."]

    def test_two_currencies_give_two_sentences(self):
        source = FakeMetricSource(comparisons=[comparison("INR", 100, 50), comparison("USD", 10, 20)])
        assert len(lines(answer(source, "compare", against="previous"))) == 2

    def test_no_data_says_so(self):
        assert lines(answer(FakeMetricSource(), "compare", against="previous")) == ["No sales were recorded in June 2026."]


class TestTrend:
    def test_a_sentence_and_a_trend_block_per_currency(self):
        source = FakeMetricSource(months=[figure()])
        result = answer(source, "trend")
        assert [block.type for block in result.blocks] == ["text", "trend"]
        assert lines(result) == ["Sales went down 4.2% from 2026-05 (INR 6,764,000) to 2026-06 (INR 6,480,000)."]
        assert result.blocks[1].data == {
            "metric": "sales", "currency": "INR", "marked": [],
            "points": [{"month": "2026-05", "value": "6764000"}, {"month": "2026-06", "value": "6480000"}],
        }

    def test_the_trend_runs_to_the_last_month_of_the_period(self):
        source = FakeMetricSource(months=[figure()])
        answer(source, "trend", LAST_YEAR)
        assert source.calls[0][3:] == (date(2025, 12, 1), 12)

    def test_a_running_month_ends_the_trend_at_this_month(self):
        source = FakeMetricSource(months=[figure()])
        answer(source, "trend", THIS_MONTH)
        assert source.calls[0][3:] == (date(2026, 11, 1), 6)

    def test_two_currencies_give_two_charts(self):
        source = FakeMetricSource(months=[figure("INR"), figure("USD")])
        assert [block.type for block in answer(source, "trend").blocks] == ["text", "trend", "trend"]

    def test_a_figure_with_no_trend_points_is_left_out(self):
        source = FakeMetricSource(months=[MonthFigure("INR", money(0), None, True, ())])
        result = answer(source, "trend")
        assert [block.type for block in result.blocks] == ["text"]
        assert lines(result) == ["No sales were recorded in June 2026."]

    def test_a_rise_from_nothing(self):
        result = answer(FakeMetricSource(months=[figure(points=((5, 0), (6, 100)))]), "trend")
        assert lines(result) == ["Sales were INR 100 in 2026-06, from nothing in 2026-05."]

    def test_a_flat_trend(self):
        result = answer(FakeMetricSource(months=[figure(points=((5, 100), (6, 100)))]), "trend")
        assert "unchanged" in lines(result)[0]


class TestRanking:
    def customers(self):
        return rows(("Alder Imports", 100), ("Kestrel Logistics", 300), ("Meridian Foods", 200))

    def test_the_leader_in_a_sentence_and_a_ranked_table(self):
        source = FakeMetricSource(comparisons=[comparison("USD", 600, 500, self.customers())])
        result = answer(source, "ranking", by="customer")
        assert [block.type for block in result.blocks] == ["text", "table"]
        assert lines(result) == ["Kestrel Logistics led sales in June 2026 at USD 300 (50.0% of USD 600)."]
        table = result.blocks[1].data
        assert table["title"] == "Top customers, June 2026"
        assert table["columns"] == ["Name", "Current"]
        assert [row["name"] for row in table["rows"]] == ["Kestrel Logistics", "Meridian Foods", "Alder Imports"]

    def test_asks_for_the_dimension_and_every_member(self):
        source = FakeMetricSource(comparisons=[comparison("USD", 600, 500, self.customers())])
        answer(source, "ranking", by="customer")
        assert source.calls[0][4:] == ("customer", 50)

    def test_keeps_only_the_top_five(self):
        many = rows(*[(f"C{index}", index * 10) for index in range(1, 9)])
        result = answer(FakeMetricSource(comparisons=[comparison("USD", 360, 0, many)]), "ranking", by="customer")
        assert [row["name"] for row in result.blocks[1].data["rows"]] == ["C8", "C7", "C6", "C5", "C4"]

    def test_members_with_nothing_in_the_period_are_not_ranked(self):
        source = FakeMetricSource(comparisons=[comparison("USD", 100, 500, rows(("Alder Imports", 100), ("Gone Ltd", 0)))])
        result = answer(source, "ranking", by="customer")
        assert [row["name"] for row in result.blocks[1].data["rows"]] == ["Alder Imports"]

    def test_a_table_per_currency_titled_with_it(self):
        source = FakeMetricSource(comparisons=[comparison("INR", 100, 0, rows(("A", 100))), comparison("USD", 50, 0, rows(("B", 50)))])
        titles = [block.data["title"] for block in answer(source, "ranking", by="customer").blocks[1:]]
        assert titles == ["Top customers, June 2026 (INR)", "Top customers, June 2026 (USD)"]

    def test_says_so_when_only_the_biggest_changes_were_read(self):
        source = FakeMetricSource(comparisons=[comparison("USD", 600, 500, self.customers(), truncated=True)])
        assert "50 customers with the biggest change" in lines(answer(source, "ranking", by="customer"))[-1]

    def test_suppliers_and_materials(self):
        source = FakeMetricSource(comparisons=[comparison("USD", 100, 0, rows(("Delta Botanicals", 100)))])
        assert answer(source, "ranking", by="supplier").blocks[1].data["title"] == "Top suppliers, June 2026"
        assert answer(source, "ranking", by="material").blocks[1].data["title"] == "Top materials, June 2026"

    def test_no_data_says_so_with_no_table(self):
        result = answer(FakeMetricSource(comparisons=[comparison("USD", 0, 0, [])]), "ranking", by="customer")
        assert [block.type for block in result.blocks] == ["text"]
        assert lines(result) == ["No sales were recorded in June 2026."]


class TestFailures:
    @pytest.mark.parametrize("response", ["value", "compare", "trend", "ranking"])
    def test_a_source_that_is_down_is_not_hidden(self, response):
        source = FakeMetricSource()
        source.down = True
        with pytest.raises(MetricsUnavailable):
            answer(source, response, against="previous" if response == "compare" else None, by="customer" if response == "ranking" else None)
