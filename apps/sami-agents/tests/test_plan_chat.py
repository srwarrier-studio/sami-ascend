import pytest

from sami_agents.application.plan_chat import BOARD_LIMIT, INLINE_LIMIT, PlanChat
from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.domain.errors import InvalidModelAnswer, ModelUnavailable
from sami_agents.infrastructure.mock_catalog_source import DEFAULT_ENTRIES
from sami_agents.infrastructure.mock_chat_model import MockChatModel


def plan(message, picks=None, error=None, catalog=DEFAULT_ENTRIES):
    model = MockChatModel(picks, error)
    return PlanChat(model).execute(message, catalog), model


def widget_ids(program):
    return [line.split('"')[1] for line in program.splitlines() if "Widget(" in line]


class TestRoute:
    def test_a_question_is_an_inline_answer_with_at_most_four_widgets(self):
        many = [CatalogEntry(f"w{n}", f"Widget {n}", "") for n in range(10)]
        program, _ = plan("show me everything", [entry.id for entry in many], catalog=many)
        assert widget_ids(program) == ["w0", "w1", "w2", "w3"][:INLINE_LIMIT]
        assert "Board(" not in program

    def test_builder_makes_a_board_of_up_to_fifteen_widgets(self):
        many = [CatalogEntry(f"w{n}", f"Widget {n}", "") for n in range(30)]
        program, _ = plan("@builder everything", [entry.id for entry in many], catalog=many)
        board = [line for line in program.splitlines() if line.startswith("board = Board(")][0]
        assert board.count('"w') == BOARD_LIMIT

    def test_builder_names_the_board_after_the_request(self):
        program, _ = plan("@builder sales overview", ["sales-today"])
        assert 'board = Board("Sales Overview", ["sales-today"])' in program

    def test_builder_without_a_request_gets_a_default_name(self):
        program, _ = plan("@builder", ["sales-today"])
        assert 'Board("AI board",' in program

    def test_the_model_does_not_see_the_builder_tag(self):
        _, model = plan("@builder sales overview", ["sales-today"])
        assert model.messages == ["sales overview"]

    def test_builder_tag_is_case_insensitive(self):
        assert "Board(" in plan("@Builder sales", ["sales-today"])[0]


class TestValidate:
    def test_unknown_ids_are_dropped(self):
        program, _ = plan("sales", ["sales-today", "made-up", "../../etc"])
        assert widget_ids(program) == ["sales-today"]

    def test_repeated_ids_are_kept_once(self):
        program, _ = plan("sales", ["sales-today", "sales-today", "day-sales"])
        assert widget_ids(program) == ["sales-today", "day-sales"]

    def test_the_order_the_model_chose_is_kept(self):
        program, _ = plan("sales", ["top-customers", "sales-today"])
        assert widget_ids(program) == ["top-customers", "sales-today"]


class TestFallback:
    @pytest.mark.parametrize("error", [ModelUnavailable(), InvalidModelAnswer()])
    def test_a_failing_model_falls_back_to_keywords(self, error):
        program, _ = plan("show top customers", error=error)
        assert widget_ids(program)[0] == "top-customers"

    def test_a_model_that_picks_nothing_falls_back_to_keywords(self):
        assert widget_ids(plan("show top customers", [])[0])[0] == "top-customers"

    def test_a_model_that_picks_only_unknown_ids_falls_back_to_keywords(self):
        assert widget_ids(plan("show top customers", ["nope"])[0])[0] == "top-customers"

    def test_a_working_model_wins_over_the_keywords(self):
        assert widget_ids(plan("show top customers", ["day-sales"])[0]) == ["day-sales"]

    def test_nothing_matching_says_so_with_no_widgets(self):
        program, _ = plan("weather in paris", error=ModelUnavailable())
        assert program.splitlines() == ["root = Stack([intro])", 'intro = Text("I could not find a matching widget.")']

    def test_the_fallback_keeps_the_builder_limit(self):
        many = [CatalogEntry(f"w{n}", "Sales report", "") for n in range(30)]
        program, _ = plan("@builder sales report", error=ModelUnavailable(), catalog=many)
        assert program.count('"w') == BOARD_LIMIT


class TestReply:
    def test_the_sentence_is_built_from_catalog_titles(self):
        program, _ = plan("sales", ["sales-today", "top-customers"])
        assert 'Text("Here is Sales today and Top customers.")' in program

    def test_three_titles_read_as_a_list(self):
        program, _ = plan("sales", ["sales-today", "day-sales", "top-customers"])
        assert 'Here is Sales today, Day sales and Top customers.' in program

    def test_a_board_sentence_counts_its_widgets(self):
        assert "I built Sales with 1 widget." in plan("@builder sales", ["sales-today"])[0]

    def test_every_program_has_a_root(self):
        for program in [plan("sales", ["sales-today"])[0], plan("zzz", error=ModelUnavailable())[0], plan("@builder x", ["day-sales"])[0]]:
            assert program.startswith("root = Stack(")

    def test_text_the_model_wrote_never_reaches_the_program(self):
        program, _ = plan("sales", ['sales-today"]) root = Evil("x', "sales-today"])
        assert "Evil" not in program
        assert widget_ids(program) == ["sales-today"]
