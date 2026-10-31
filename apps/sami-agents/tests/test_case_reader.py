from datetime import date

import pytest

from sami_agents.application.case_reader import CaseReader
from sami_agents.application.question_reader import QuestionReader, correct_months
from sami_agents.domain.entities.question import Question
from sami_agents.infrastructure.mock_case_model import MockCaseModel
from sami_agents.infrastructure.understanding_loader import load_understanding

TODAY = date(2026, 10, 31)
RULES = QuestionReader(load_understanding())


def reader(answers=None, failing=False, min_confidence=0.5):
    model = MockCaseModel(answers if answers is not None else {}, failing)
    return CaseReader(RULES, model, min_confidence), model


def why(metric="sales", direction="fall", confidence=0.9):
    return {"intent": ("why", confidence), "subject": (metric, confidence), "direction": (direction, confidence)}


class TestReadByTheModel:
    def test_the_passes_build_the_case_and_the_question(self):
        result = reader(why())[0].read("Why did sales drop in august", TODAY)
        assert result.question == Question("sales", "fall", date(2026, 8, 1), "why")
        assert (result.case.intent, result.case.metric, result.case.direction, result.case.month, result.case.scope) == ("why", "sales", "fall", date(2026, 8, 1), "all")
        assert result.case.how_read == ["intent: why", "subject: sales", "direction: fall"]

    def test_the_model_decides_what_the_rules_cannot(self):
        result = reader(why("purchases", "rise"))[0].read("why did we spend more in june", TODAY)
        assert result.question == Question("purchases", "rise", date(2026, 6, 1), "why")

    def test_a_figure_question_skips_the_direction_pass(self):
        answers = {"intent": ("figure", 0.9), "subject": ("sales", 0.9)}
        read, model = reader(answers)
        result = read.read("how did sales do in august", TODAY)
        assert result.question == Question("sales", "change", date(2026, 8, 1), "figure")
        assert [call[0] for call in model.calls] == ["intent", "subject"]

    def test_a_figure_may_ask_about_the_current_month_and_a_why_may_not(self):
        figure = reader({"intent": ("figure", 0.9), "subject": ("sales", 0.9)})[0].read("what are sales this month", TODAY)
        assert figure.question.month == date(2026, 10, 1)
        refused = reader(why())[0].read("why did sales fall this month", TODAY)
        assert (refused.question, refused.problem) == (None, "not_finished")


class TestStoppingEarly:
    def test_an_unrelated_question_stops_at_the_first_pass(self):
        read, model = reader({"intent": ("other", 0.8)})
        result = read.read("tell me a joke", TODAY)
        assert (result.question, result.problem) == (None, "unreadable")
        assert [call[0] for call in model.calls] == ["intent"]

    def test_a_widget_request_stops_at_the_first_pass_and_says_so(self):
        read, model = reader({"intent": ("widgets", 0.8)})
        assert read.read("show me top customers", TODAY).problem == "widgets"
        assert len(model.calls) == 1

    def test_no_subject_is_refused(self):
        answers = why()
        answers["subject"] = ("none", 0.9)
        read, model = reader(answers)
        assert read.read("why did the moon change in august", TODAY).problem == "unreadable"
        assert [call[0] for call in model.calls] == ["intent", "subject"]


class TestUnsureMeansTheRules:
    def test_a_pass_below_the_confidence_is_read_by_the_rules(self):
        answers = {"intent": ("other", 0.3), "subject": ("purchases", 0.2), "direction": ("rise", 0.4)}
        result = reader(answers)[0].read("why did sales fall in august", TODAY)
        assert result.question == Question("sales", "fall", date(2026, 8, 1), "why")
        assert result.case.how_read[:3] == ["intent: unsure, read by rules", "subject: unsure, read by rules", "direction: unsure, read by rules"]

    def test_a_sure_none_is_overruled_by_a_word_that_names_a_metric(self):
        answers = why()
        answers["subject"] = ("none", 0.9)
        result = reader(answers)[0].read("what made turnover increase in may", TODAY)
        assert result.question == Question("sales", "fall", date(2026, 5, 1), "why")
        assert "subject: the word for sales overruled the model" in result.case.how_read

    def test_unsure_and_the_rules_cannot_read_it_either_is_refused_not_guessed(self):
        result = reader({"intent": ("other", 0.3)})[0].read("sales are weird lately", TODAY)
        assert (result.question, result.problem) == (None, "unreadable")

    def test_the_confidence_is_a_setting(self):
        answers = why(confidence=0.6)
        assert reader(answers, min_confidence=0.7)[0].read("why did sales fall in august", TODAY).case.how_read[0] == "intent: unsure, read by rules"
        assert reader(answers, min_confidence=0.5)[0].read("why did sales fall in august", TODAY).case.how_read[0] == "intent: why"


class TestWhenTheModelIsDown:
    @pytest.mark.parametrize("text", ["why did sales fall in august", "show me top customers", "why did sales to Acme drop in august", "what were sales for august"])
    def test_the_rules_answer_exactly_as_before(self, text):
        assert reader(failing=True)[0].read(text, TODAY) == RULES.read(text, TODAY)

    def test_a_model_that_fails_part_way_also_falls_back(self):
        assert reader({"intent": ("why", 0.9)})[0].read("why did sales fall in august", TODAY) == RULES.read("why did sales fall in august", TODAY)


class TestTheMonth:
    @pytest.mark.parametrize("text", ["Why did sales drop in Augsut?", "why did sales drop in agust", "why did sales drop in septmber", "why did sales drop in Decmber"])
    def test_a_mistyped_month_is_still_read(self, text):
        assert reader(why())[0].read(text, TODAY).question is not None

    @pytest.mark.parametrize("text,fixed", [("augsut", "august"), ("septmber", "september"), ("match", "match"), ("august", "august"), ("augment", "augment"), ("remember", "remember"), ("number", "number"), ("marketing", "marketing"), ("decide", "decide")])
    def test_only_close_month_names_are_corrected(self, text, fixed):
        assert correct_months(text) == fixed

    @pytest.mark.parametrize("text", ["why did sales drop last quarter", "why did sales drop this year", "why did sales fall last week", "why did sales fall in Q3", "why did sales fall yesterday"])
    def test_other_periods_are_refused_as_not_one_month(self, text):
        assert reader(why())[0].read(text, TODAY).problem == "not_one_month"

    def test_a_question_with_no_period_at_all_is_unreadable(self):
        assert reader(why())[0].read("why did sales fall", TODAY).problem == "unreadable"

    def test_a_month_wins_over_a_period_word(self):
        assert reader(why())[0].read("why did sales fall in august this year", TODAY).question.month == date(2026, 8, 1)


class TestScope:
    @pytest.mark.parametrize("text", [
        "why did sales to Acme drop in august", "why did sales of steel plate fall in august", "why did purchases from Doosan rise in july",
        "why did sales in the Pune plant fall in august", "why did revenue from eastern castings drop in august", "what were sales for steel in august",
    ])
    def test_a_question_about_one_name_is_refused_not_answered_as_the_total(self, text):
        result = reader({**why("sales"), **why("purchases")})[0].read(text, TODAY)
        assert (result.question, result.problem, result.case.scope) == (None, "restricted", "restricted")

    @pytest.mark.parametrize("text", [
        "why did sales drop in august", "why are sales so low in september", "what pushed sales up in july", "why did we spend more in june",
        "why did sales to our customers drop in august", "why did sales fall at the end of august", "why did sales drop by 10% in august",
        "why did sales fall in august 2026", "why did sales go down in the last month", "how much did we buy from suppliers in june",
        "why did sales fall during august", "what were sales for august", "why did the sales of august fall",
    ])
    def test_a_whole_company_question_is_not_refused(self, text):
        result = reader({"intent": ("why", 0.9), "subject": ("sales", 0.9), "direction": ("fall", 0.9)})[0].read(text, TODAY)
        assert result.problem != "restricted", text
