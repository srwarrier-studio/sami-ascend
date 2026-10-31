from datetime import date
from decimal import Decimal

import pytest
from test_analyse_question import GRAPH, INFOS, TestWalkingAndTheCauses as Data, row, total, with_rows

from sami_agents.application.analyse_question import AnalyseQuestion
from sami_agents.application.answer_question import MOCK_LABEL, AnswerQuestion
from sami_agents.application.question_reader import HELP, NOT_FINISHED, QuestionReader
from sami_agents.domain.entities.measure import TrendPoint
from sami_agents.domain.errors import DataUnavailable
from sami_agents.domain.gateways.question_model import LineRewriter, QuestionModel
from sami_agents.infrastructure.mock_data_source import MockDataSource
from sami_agents.infrastructure.understanding_loader import load_understanding

TODAY = date(2026, 10, 31)
GRAND = total("6480000", "7570000")
TREND = [TrendPoint(f"2026-0{m}", Decimal(7000000 + m)) for m in range(3, 9)]


def source(records=None, trends=None, comparisons=None):
    acme = row("ACME", "100000", "900000", "73.4", name="Acme Industries")
    base = {("sales", None): [GRAND], ("sales", "customer"): [with_rows(GRAND, [acme])], ("sales", "material"): [with_rows(GRAND, [row("M", "1", "1", "0")])]}
    return MockDataSource(records if records is not None else {"contract": [Data.CONTRACT]}, None, INFOS, comparisons if comparisons is not None else base, trends if trends is not None else {"sales": TREND})


def answerer(data=None, mock=True, model=None, rewriter=None, tone="plain"):
    data = data or source()
    return AnswerQuestion(QuestionReader(load_understanding()), AnalyseQuestion(data, GRAPH), data, ["sales", "purchases"], mock, model, rewriter, tone=tone)


def ask(text="Why did sales fall in August?", **kwargs):
    return answerer(**kwargs).execute(text, "tok", TODAY)


class TestAReadableQuestion:
    def test_it_says_how_it_understood_the_question(self):
        assert ask()["question"] == {"metric": "sales", "intent": "why", "direction": "fall", "month": "2026-08", "compared_with": "2026-07", "scope": "all", "how_read": []}

    def test_the_blocks_are_text_then_trend_then_the_tables_then_the_evidence(self):
        assert [b["type"] for b in ask()["blocks"]] == ["text", "trend", "table", "table", "evidence"]

    def test_the_text_block_holds_the_headline_the_finding_and_its_cause(self):
        lines = ask()["blocks"][0]["lines"]
        assert lines[0].startswith("Sales fell 14.4% from July 2026 to August 2026")
        assert lines[1].startswith("Acme Industries fell")
        assert "no valid contract" in lines[2] and "0040000127" in lines[2]

    def test_the_trend_block_has_six_months_and_marks_the_two_compared(self):
        trend = ask()["blocks"][1]
        assert (trend["metric"], trend["currency"], len(trend["points"]), trend["marked"]) == ("sales", "INR", 6, ["2026-07", "2026-08"])
        assert trend["points"][0] == {"month": "2026-03", "value": "7000003"}

    def test_the_tables_are_by_dimension_with_the_rows_as_json(self):
        tables = [b for b in ask()["blocks"] if b["type"] == "table"]
        assert [t["title"] for t in tables] == ["By customer", "By material"]
        assert tables[0]["rows"][0]["key"] == "ACME" and tables[0]["rows"][0]["current"] == "100000"

    def test_the_evidence_block_has_each_step_with_its_sentence_and_the_rows(self):
        [evidence] = [b for b in ask()["blocks"] if b["type"] == "evidence"]
        [step] = evidence["steps"]
        assert (evidence["finding"], step["node"], step["kind"]) == ("Acme Industries", "Contract", "coverage_gap")
        assert "0040000127" in step["summary"] and step["rows"][0]["SalesContract"] == "0040000127"

    def test_the_machine_readable_analysis_carries_figures_findings_and_cause_tags(self):
        analysis = ask()["analysis"]
        assert (analysis["currency"], analysis["current"], analysis["significant"], analysis["change_percent"]) == ("INR", "6480000", True, "-14.40")
        [finding] = analysis["findings"]
        assert finding["causes"] == [{"source": "record:contract", "kind": "coverage_gap", "key": "0040000127"}]
        assert finding["paths"][0][0]["numbers"]["first_uncovered"] == "2026-07-13" and finding["share_percent"] == "73.4"

    def test_the_mock_label_is_there_until_the_data_is_real(self):
        assert ask()["label"] == MOCK_LABEL and ask(mock=False)["label"] is None

    def test_the_wording_never_says_caused(self):
        assert "caused" not in " ".join(ask()["blocks"][0]["lines"])

    def test_a_trend_that_cannot_be_loaded_is_left_out_and_said(self):
        data = source()
        data.trend = lambda *a, **k: (_ for _ in ()).throw(DataUnavailable("down"))
        answer = ask(data=data)
        assert "trend" not in [b["type"] for b in answer["blocks"]]
        assert "could not be loaded" in " ".join(answer["blocks"][0]["lines"])

    def test_no_data_gives_just_the_text(self):
        answer = ask(data=source(comparisons={}))
        assert [b["type"] for b in answer["blocks"]] == ["text"] and "no data" in answer["blocks"][0]["lines"][0].lower()

    def test_a_failing_source_is_unavailable(self):
        data = source()
        data.fail()
        with pytest.raises(DataUnavailable):
            ask(data=data)


class TestAFigureQuestion:
    def test_it_is_a_sentence_and_a_trend_with_no_analysis(self):
        answer = ask("What are the sales for August?")
        assert answer["question"] == {"metric": "sales", "intent": "figure", "direction": "change", "month": "2026-08", "compared_with": "2026-07", "scope": "all", "how_read": []}
        assert [b["type"] for b in answer["blocks"]] == ["text", "trend"] and answer["analysis"] is None
        assert answer["blocks"][0]["lines"][0].startswith("Sales for August 2026 were INR 6,480,000, down 14.4%")
        assert (len(answer["blocks"][1]["points"]), answer["blocks"][1]["marked"]) == (6, ["2026-07", "2026-08"])

    def test_the_label_is_there_while_the_data_is_mock(self):
        assert ask("What are the sales for August?")["label"] == MOCK_LABEL

    def test_the_current_month_is_so_far_with_one_month_marked(self):
        answer = ask("what are sales this month")
        assert answer["question"]["compared_with"] is None and answer["blocks"][1]["marked"] == ["2026-10"]
        assert "so far this month" in answer["blocks"][0]["lines"][0]

    def test_a_month_with_no_data_is_one_sentence(self):
        answer = ask("What are the sales for August?", data=source(comparisons={}))
        assert answer["blocks"] == [{"type": "text", "lines": ["No sales were recorded in August 2026."]}]

    def test_a_trend_that_cannot_be_loaded_is_said(self):
        data = source()
        data.trend = lambda *a, **k: (_ for _ in ()).throw(DataUnavailable("down"))
        answer = ask("What are the sales for August?", data=data)
        assert [b["type"] for b in answer["blocks"]] == ["text"] and "could not be loaded" in answer["blocks"][0]["lines"][-1]

    def test_a_failing_source_is_unavailable(self):
        data = source()
        data.fail()
        with pytest.raises(DataUnavailable):
            ask("What are the sales for August?", data=data)


class TestAQuestionItCannotAnswer:
    @pytest.mark.parametrize("text,message", [("show me sales", HELP), ("why did sales fall this month", NOT_FINISHED)])
    def test_the_reply_says_what_can_be_asked_and_nothing_else(self, text, message):
        answer = ask(text)
        assert (answer["readable"], answer["question"], answer["analysis"], answer["blocks"]) == (False, None, None, [{"type": "text", "lines": [message]}])

    def test_the_problem_says_which_kind_it_is(self):
        assert ask("show me sales")["problem"] == "unreadable"
        assert ask("why did sales fall this month")["problem"] == "not_finished"


class FixedModel(QuestionModel):
    def __init__(self, answer):
        self.answer, self.calls = answer, 0

    def read(self, text, metrics):
        self.calls += 1
        return self.answer


class TestTheOptionalReader:
    def test_it_is_used_only_when_the_rules_cannot_read_the_question(self):
        model = FixedModel({"metric": "sales", "direction": "fall", "month": "2026-08"})
        assert ask(model=model)["readable"] and model.calls == 0
        answer = ask("sales numbers went wonky around the summer holidays?", model=model)
        assert model.calls == 1 and answer["question"]["month"] == "2026-08"

    def test_a_checked_answer_from_the_model_is_used(self):
        model = FixedModel({"metric": "sales", "direction": "fall", "month": "2026-08"})
        answer = ask("what the heck happened to the money coming in last summer", model=model)
        assert answer["readable"] is True and answer["question"] == {"metric": "sales", "intent": "why", "direction": "fall", "month": "2026-08", "compared_with": "2026-07", "scope": "all", "how_read": []}

    @pytest.mark.parametrize("bad", [None, {"metric": "weather", "direction": "fall", "month": "2026-08"}, {"metric": "sales", "direction": "fall", "month": "2027-05"}, "text"])
    def test_a_bad_answer_leaves_the_question_unreadable(self, bad):
        answer = ask("what the heck happened to the money lately", model=FixedModel(bad))
        assert (answer["readable"], answer["blocks"][0]["lines"]) == (False, [HELP])

    def test_the_model_is_not_asked_about_a_month_that_is_not_over(self):
        model = FixedModel({"metric": "sales", "direction": "fall", "month": "2026-08"})
        assert ask("why did sales fall this month", model=model)["blocks"][0]["lines"] == [NOT_FINISHED] and model.calls == 0


class FixedRewriter(LineRewriter):
    def __init__(self, text=None, by_line=None):
        self.text, self.by_line, self.calls = text, by_line or {}, []

    def rewrite(self, line, tone):
        self.calls.append((line, tone))
        return self.by_line.get(line, self.text)


HEADLINE = "Sales fell 14.4% from July 2026 to August 2026 (INR 7,570,000 to INR 6,480,000)."


class TestTheOptionalRewrite:
    def test_the_templates_stay_when_the_tone_is_plain_and_the_model_is_never_asked(self):
        rewriter = FixedRewriter("Sales dropped.")
        assert ask(rewriter=rewriter)["blocks"][0]["lines"][0].startswith("Sales fell 14.4% from July 2026")
        assert rewriter.calls == []

    def test_every_text_line_is_rewritten_alone_with_the_tone(self):
        rewriter = FixedRewriter(by_line={})
        lines = ask(rewriter=rewriter, tone="executive")["blocks"][0]["lines"]
        assert [call[0] for call in rewriter.calls] == lines and {call[1] for call in rewriter.calls} == {"executive"}

    def test_a_line_that_keeps_every_figure_and_name_is_used(self):
        data = source()
        plain = ask(data=data)["blocks"][0]["lines"]
        text = plain[0].replace("Sales fell", "Sales dropped by")
        shown = ask(data=data, rewriter=FixedRewriter(by_line={plain[0]: text}), tone="friendly")["blocks"][0]["lines"]
        assert shown[0] == text and shown[1:] == plain[1:]

    def test_a_bad_line_keeps_its_template_and_the_others_still_change(self):
        data = source()
        plain = ask(data=data)["blocks"][0]["lines"]
        good = plain[1].replace(" fell ", " dropped by ")
        shown = ask(data=data, rewriter=FixedRewriter(by_line={plain[0]: "Sales fell 20% from July 2026 to August 2026.", plain[1]: good}), tone="executive")["blocks"][0]["lines"]
        assert shown[0] == plain[0] and shown[1] == good

    @pytest.mark.parametrize("bad", ["Sales fell 14.4% in August thanks to Acme.", "Sales fell 14.4% from July to August.", "Great job! Sales fell 14.4% from July 2026 to August 2026 (INR 7,570,000 to INR 6,480,000).", "**Sales** fell", "", None])
    def test_a_line_that_adds_drops_or_marks_up_a_figure_or_name_is_dropped(self, bad):
        plain = ask()["blocks"][0]["lines"]
        assert ask(rewriter=FixedRewriter(by_line={plain[0]: bad}), tone="executive")["blocks"][0]["lines"][0] == plain[0]

    def test_a_figure_answer_is_rewritten_the_same_way(self):
        plain = ask("What are the sales for August?")["blocks"][0]["lines"]
        rewriter = FixedRewriter(by_line={})
        ask("What are the sales for August?", rewriter=rewriter, tone="friendly")
        assert [call[0] for call in rewriter.calls] == plain


class TestWithTheCaseReader:
    def asker(self, answers, text):
        from sami_agents.application.case_reader import CaseReader
        from sami_agents.infrastructure.mock_case_model import MockCaseModel

        data = source()
        reader = CaseReader(QuestionReader(load_understanding()), MockCaseModel(answers))
        return AnswerQuestion(reader, AnalyseQuestion(data, GRAPH), data, ["sales", "purchases"]).execute(text, "tok", TODAY)

    WHY = {"intent": ("why", 0.9), "subject": ("sales", 0.9), "direction": ("fall", 0.9)}

    def test_the_answer_says_how_the_question_was_read(self):
        answer = self.asker(self.WHY, "Why did sales drop in Augsut?")
        assert answer["readable"] is True
        assert answer["question"] == {"metric": "sales", "intent": "why", "direction": "fall", "month": "2026-08", "compared_with": "2026-07", "scope": "all", "how_read": ["intent: why", "subject: sales", "direction: fall"]}

    def test_a_restricted_question_is_refused_with_its_own_problem_and_text(self):
        from sami_agents.application.case_reader import RESTRICTED

        answer = self.asker(self.WHY, "why did sales to Acme drop in august")
        assert (answer["readable"], answer["problem"], answer["blocks"]) == (False, "restricted", [{"type": "text", "lines": [RESTRICTED]}])

    def test_another_period_is_refused_as_not_one_month(self):
        answer = self.asker(self.WHY, "why did sales drop last quarter")
        assert (answer["problem"], "one month at a time" in answer["blocks"][0]["lines"][0]) == ("not_one_month", True)

    def test_a_widget_request_is_reported_so_the_page_can_use_its_planner(self):
        answer = self.asker({"intent": ("widgets", 0.9)}, "show me top customers")
        assert (answer["readable"], answer["problem"]) == (False, "widgets")


class TestBuildingTheAnalyst:
    def test_laya_is_used_only_when_its_url_is_set(self):
        from sami_agents.application.case_reader import CaseReader
        from sami_agents.entrypoint.analyst import build_analyst
        from sami_agents.infrastructure.settings import Settings

        assert type(build_analyst(Settings(_env_file=None, laya_url=""), source()).reader) is QuestionReader
        assert type(build_analyst(Settings(_env_file=None, laya_url="http://localhost:8000"), source()).reader) is CaseReader
