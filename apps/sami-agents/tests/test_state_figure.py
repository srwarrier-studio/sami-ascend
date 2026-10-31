import re
from datetime import date
from decimal import Decimal

import pytest
from test_analyse_question import INFOS, total

from sami_agents.application import wording
from sami_agents.application.state_figure import StateFigure
from sami_agents.domain.entities.question import Question
from sami_agents.domain.errors import DataUnavailable
from sami_agents.infrastructure.mock_data_source import MockDataSource

TODAY = date(2026, 10, 31)
AUGUST = Question("sales", "change", date(2026, 8, 1), "figure")


def figure(current, previous, question=AUGUST):
    data = MockDataSource(None, None, INFOS, {("sales", None): [total(current, previous)]} if current is not None else {})
    return StateFigure(data).execute(question, "tok", TODAY)


def lines(current, previous, question=AUGUST):
    return wording.figure_lines(figure(current, previous, question))


class TestTheSentence:
    def test_a_fall_is_significant_and_points_to_the_reasons(self):
        assert lines("6480000", "7570000") == [
            "Sales for August 2026 were INR 6,480,000, down 14.4% from July 2026 (INR 7,570,000).",
            "Ask why sales fell in August for the reasons.",
        ]

    def test_a_rise(self):
        assert lines("8000000", "5000000")[0] == "Sales for August 2026 were INR 8,000,000, up 60.0% from July 2026 (INR 5,000,000)."

    def test_a_small_change_does_not_point_to_the_reasons(self):
        assert len(lines("1010", "1000")) == 1

    def test_an_unchanged_month(self):
        assert lines("1000", "1000") == ["Sales for August 2026 were INR 1,000, unchanged from July 2026 (INR 1,000)."]

    def test_a_previous_month_of_zero_has_no_percent(self):
        assert lines("1000", "0")[0] == "Sales for August 2026 were INR 1,000, up from nothing in July 2026."

    def test_a_month_with_no_rows(self):
        assert lines("0", "0") == ["No sales were recorded in August 2026."]
        assert lines(None, None) == ["No sales were recorded in August 2026."]

    def test_the_current_month_is_so_far_with_no_comparison(self):
        october = Question("sales", "change", date(2026, 10, 1), "figure")
        assert lines("500", "1000", october) == ["Sales so far this month (October 2026) were INR 500."]
        assert lines("0", "1000", october) == ["No sales were recorded in October 2026."]


class TestEverythingIsFromTheFigure:
    @pytest.mark.parametrize("current,previous", [("6480000", "7570000"), ("8000000", "5000000"), ("1000", "0"), ("12345.5", "999")])
    def test_each_number_is_in_the_figure(self, current, previous):
        f = figure(current, previous)
        allowed = {wording.number(f.current), wording.number(f.previous), wording.percent_text(f.change_percent).rstrip("%"), "2026"}
        for number in re.findall(r"\d[\d,]*\.?\d*", " ".join(wording.figure_lines(f))):
            assert number.rstrip(".,") in allowed, number


class TestData:
    def test_an_unregistered_metric_is_unavailable(self):
        with pytest.raises(DataUnavailable):
            StateFigure(MockDataSource()).execute(AUGUST, "tok", TODAY)

    def test_a_failing_source_is_unavailable(self):
        data = MockDataSource(None, None, INFOS)
        data.failing = True
        with pytest.raises(DataUnavailable):
            StateFigure(data).execute(AUGUST, "tok", TODAY)
