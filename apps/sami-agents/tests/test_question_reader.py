import json
from datetime import date

import pytest

from sami_agents.application.question_reader import HELP, QuestionReader
from sami_agents.domain.entities.question import Question
from sami_agents.infrastructure.registry_info_loader import load_registry_info
from sami_agents.infrastructure.settings import REGISTRY_FILE
from sami_agents.infrastructure.understanding_loader import UNDERSTANDING_FILE, load_understanding

TODAY = date(2026, 10, 31)
WORDS = load_understanding()
READER = QuestionReader(WORDS)


def read(text, today=TODAY):
    return READER.read(text, today)


class TestReadable:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("why did sales fall in August", Question("sales", "fall", date(2026, 8, 1))),
            ("Why did purchases go up in September 2026?", Question("purchases", "rise", date(2026, 9, 1))),
            ("what made revenue drop last month", Question("sales", "fall", date(2026, 9, 1))),
            ("Why did sales change in March?", Question("sales", "change", date(2026, 3, 1))),
            ("why were purchases higher in aug", Question("purchases", "rise", date(2026, 8, 1))),
            ("explain why procurement increased in July", Question("purchases", "rise", date(2026, 7, 1))),
            ("why is spend different in june 2025", Question("purchases", "change", date(2025, 6, 1))),
            ("  WHY   did   SALES   fell  in  AUGUST  ", Question("sales", "fall", date(2026, 8, 1))),
        ],
    )
    def test_the_question_is_read(self, text, expected):
        assert read(text).question == expected

    def test_a_month_later_in_the_year_than_today_means_last_year(self):
        assert read("why did sales fall in December").question.month == date(2025, 12, 1)

    def test_last_month_in_january_is_december(self):
        assert read("why did sales fall last month", date(2027, 1, 15)).question.month == date(2026, 12, 1)

    def test_the_first_direction_word_wins(self):
        assert read("why did sales rise then fall in August").question.direction == "rise"

    def test_the_first_metric_wins(self):
        assert read("why did purchases rise while sales fell in August").question.metric == "purchases"


class TestFigure:
    @pytest.mark.parametrize(
        "text,expected",
        [
            ("What are the sales for August?", Question("sales", "change", date(2026, 8, 1), "figure")),
            ("how much did we purchase in September 2026", Question("purchases", "change", date(2026, 9, 1), "figure")),
            ("what were purchases last month", Question("purchases", "change", date(2026, 9, 1), "figure")),
            ("what are sales this month", Question("sales", "change", date(2026, 10, 1), "figure")),
        ],
    )
    def test_the_figure_is_asked_for(self, text, expected):
        assert read(text).question == expected

    def test_a_metric_and_a_month_alone_is_a_figure(self):
        assert read("sales in August").question == Question("sales", "change", date(2026, 8, 1), "figure")
        assert read("compare july and august sales").question is None

    def test_a_why_word_wins(self):
        assert read("what made sales fall in August").question.intent == "why"

    def test_a_figure_needs_a_metric_and_a_month(self):
        assert read("what are the sales").question is None and read("what is in August").question is None


class TestUnreadable:
    @pytest.mark.parametrize("text", ["show me sales", "why is the sky blue", "why did sales fall", "why did it fall in August", ""])
    def test_it_does_not_guess(self, text):
        result = read(text)
        assert (result.question, result.problem) == (None, "unreadable")

    def test_the_help_text_names_what_can_be_asked(self):
        assert "why a metric rose or fell in a month" in HELP and "sales" in HELP


class TestMonthsThatAreNotOver:
    @pytest.mark.parametrize("text", ["why did sales fall this month", "why did sales fall in October", "why did sales fall in October 2026", "why did sales fall in November 2026"])
    def test_they_are_refused_with_a_reason(self, text):
        assert (read(text).question, read(text).problem) == (None, "not_finished")

    def test_a_finished_month_of_this_year_is_fine(self):
        assert read("why did sales fall in September").question is not None


class TestTheWordFile:
    def test_every_registered_metric_has_words(self):
        registered = set(load_registry_info(REGISTRY_FILE).metrics)
        assert registered <= set(WORDS.metrics), registered - set(WORDS.metrics)

    def test_a_metric_that_is_not_registered_is_not_listed(self):
        assert set(WORDS.metrics) <= set(load_registry_info(REGISTRY_FILE).metrics)

    def test_a_badly_shaped_file_is_refused(self, tmp_path):
        path = tmp_path / "u.json"
        path.write_text(json.dumps({"metrics": {"sales": "sales"}, "why": ["why"], "figure": ["what"], "rise": ["up"], "fall": ["down"], "change": ["change"]}))
        with pytest.raises(ValueError):
            load_understanding(path)
        assert UNDERSTANDING_FILE.name == "understanding.json"
