from datetime import date
from decimal import Decimal

import pytest
from test_analyse_question import GRAND, GRAPH, INFOS, TODAY, covering, fall_by_customer, row, total, with_rows

from intent_api.application.analysis import why_wording
from intent_api.application.analysis.answer_why import NEEDS_A_FINISHED_MONTH, AnswerWhy
from intent_api.application.read_currency import read_currency
from intent_api.domain.analysis.measure import TrendPoint
from intent_api.domain.entities.answer import AnswerRule
from intent_api.domain.entities.period import Period
from intent_api.domain.errors import MetricsUnavailable
from intent_api.infrastructure.mock_data_source import MockDataSource

RULE = AnswerRule("sales_why", "why", "sales")
AUGUST = Period("month", 2026, 8, date(2026, 8, 1), date(2026, 8, 31), True, "August 2026")
ROWS = [row("A", "100", "1000", "80")]
TRENDS = {"sales": [TrendPoint("2026-07", Decimal(1000)), TrendPoint("2026-08", Decimal(900))]}


def source(comparisons=None):
    return MockDataSource({"contract": covering("A")}, None, INFOS, comparisons or fall_by_customer(ROWS), TRENDS)


def answer(company="all", currency=None, period=AUGUST, mock=None):
    mock = mock or source()
    return AnswerWhy(mock, GRAPH).execute(RULE, period, "tok", TODAY, company, currency), mock


def types(blocks):
    return [block.type for block in blocks]


class TestTheBlocks:
    def test_a_headline_a_trend_a_table_and_the_evidence(self):
        blocks, _ = answer()
        assert types(blocks)[:2] == ["findings", "trend"] and "table" in types(blocks)

    def test_the_first_sentence_names_the_scope_and_the_currency(self):
        text = answer("sabinsa")[0][0].data["headline"]
        assert text.startswith("Sales of Sami-Sabinsa fell 10.0% in August 2026, to INR 900 from INR 1K")

    def test_the_group_says_all_companies_and_warns_about_the_dilution(self):
        data = answer("all")[0][0].data
        assert data["headline"].startswith("Sales of all your companies fell") and data["notes"][-1] == why_wording.GROUP_LIMIT

    def test_a_single_company_has_no_group_warning(self):
        assert why_wording.GROUP_LIMIT not in answer("organica")[0][0].data["notes"]

    def test_the_trend_is_marked_with_the_two_months(self):
        blocks, mock = answer()
        trend = next(b for b in blocks if b.type == "trend")
        assert trend.data["currency"] == "INR" and trend.data["marked"] == ["2026-07", "2026-08"]


class TestScopeAndCurrency:
    def test_a_company_is_sent_to_every_read_and_all_sends_none(self):
        _, mock = answer("organica")
        assert mock.companies == ["organica"]
        _, mock = answer("all")
        assert mock.companies == [None]

    def test_the_currency_with_the_biggest_change_is_used(self):
        comparisons = {**fall_by_customer(ROWS), ("sales", None): [GRAND, total("40", "100", "USD")]}
        data = answer(mock=source(comparisons))[0][0].data
        assert "to USD 40 from USD 100" in data["headline"] and any("also changed" in line and "INR" in line for line in data["notes"])

    def test_a_named_currency_is_answered_in_that_currency(self):
        comparisons = {**fall_by_customer(ROWS), ("sales", None): [GRAND, total("40", "100", "USD")]}
        assert "INR" in answer(currency="INR", mock=source(comparisons))[0][0].data["headline"]

    def test_a_currency_without_data_says_so(self):
        assert "no data in USD" in answer(currency="USD")[0][0].data["lines"][0]


class TestRefusals:
    @pytest.mark.parametrize("period", [
        Period("month", 2026, 10, date(2026, 10, 1), date(2026, 10, 31), False, "October 2026"),
        Period("year", 2026, None, date(2026, 1, 1), date(2026, 12, 31), False, "2026"),
        Period("year", 2025, None, date(2025, 1, 1), date(2025, 12, 31), True, "2025"),
    ])
    def test_only_a_finished_month_is_analysed(self, period):
        blocks, mock = answer(period=period)
        assert [b.data for b in blocks] == [{"lines": [NEEDS_A_FINISHED_MONTH]}] and mock.calls == []

    def test_an_unregistered_metric_is_unavailable(self):
        with pytest.raises(MetricsUnavailable):
            answer(mock=MockDataSource())

    def test_a_failing_source_is_unavailable(self):
        mock = source()
        mock.fail()
        with pytest.raises(MetricsUnavailable):
            answer(mock=mock)

    def test_no_data_says_so_without_blocks_besides_the_sentence(self):
        blocks, _ = answer(mock=source({("sales", None): []}))
        assert types(blocks) == ["text"]


class TestReadingTheCurrency:
    @pytest.mark.parametrize("text,expected", [
        ("why did sales fall in August in USD", "USD"), ("why did sales fall in rupees", "INR"), ("why did sales fall in August", None),
        ("sales in dollars", "USD"), ("sales in ₹ last month", "INR"), ("usd or inr", None), ("sales for Mars", None),
    ])
    def test_a_currency_word_names_the_currency(self, text, expected):
        assert read_currency(text) == expected


class TestTheFindingsBlock:
    def test_a_mover_reads_as_a_plain_line(self):
        item = answer("sabinsa")[0][0].data["items"][0]
        assert item["name"] == "Name A" and item["role"] == "mover" and item["direction"] == "down" and item["dimension"] == "customer"
        assert item["detail"] == "down INR 900 (90.0%), 80.0% of the total fall"

    def test_the_headline_is_plain_and_short(self):
        assert answer("sabinsa")[0][0].data["headline"] == "Sales of Sami-Sabinsa fell 10.0% in August 2026, to INR 900 from INR 1K in July 2026."

    def test_coverage_is_one_plain_sentence(self):
        assert answer("sabinsa")[0][0].data["coverage"]["text"] == "We found no cause for this in the data we hold."
        gap = MockDataSource({"contract": []}, None, INFOS, fall_by_customer(ROWS), TRENDS)
        coverage = answer("sabinsa", mock=gap)[0][0].data["coverage"]
        assert coverage["text"].startswith("We can explain about ") and Decimal(coverage["explained_percent"]) > 0

    def test_a_refusal_stays_one_text_block(self):
        blocks, _ = answer(period=Period("month", 2026, 11, date(2026, 11, 1), date(2026, 11, 30), False, "November 2026"))
        assert [b.type for b in blocks] == ["text"]

    def test_a_cause_is_one_reason_sentence_and_no_cause_is_no_reason(self):
        assert answer("sabinsa")[0][0].data["items"][0]["reasons"] == []
        gap = MockDataSource({"contract": []}, None, INFOS, fall_by_customer(ROWS), TRENDS)
        reasons = answer("sabinsa", mock=gap)[0][0].data["items"][0]["reasons"]
        assert reasons and reasons[0].startswith("Possible reason: there was no valid contract for ")

    def test_amounts_are_short_and_dates_read_naturally(self):
        from intent_api.application.analysis.why_wording import compact, day_text

        assert [compact(Decimal(v)) for v in ("999", "1000", "113578.37", "2500000", "1200000000")] == ["999", "1K", "113.6K", "2.5M", "1.2B"]
        assert day_text("2026-08-02") == "2 Aug 2026"
