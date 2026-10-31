import pytest

from sami_agents.application.keyword_matcher import KeywordMatcher
from sami_agents.application.plan_chat import BOARD_CHECKS, BOARD_LIMIT, INLINE_CHECKS, INLINE_LIMIT, PlanChat, board_name_from
from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.domain.errors import ReplyUnavailable
from sami_agents.infrastructure.mock_catalog_source import DEFAULT_ENTRIES
from sami_agents.infrastructure.mock_relevance_checker import MockRelevanceChecker
from sami_agents.infrastructure.mock_reply_writer import MockReplyWriter


def reports(count: int) -> list[CatalogEntry]:
    return [CatalogEntry(f"w{n:02d}", f"Report {n:02d}", "") for n in range(count)]


def run(message, checker=None, catalog=None, **options):
    return PlanChat(checker, **options).run(message, DEFAULT_ENTRIES if catalog is None else catalog)


def widget_ids(program):
    return [line.split('"')[1] for line in program.splitlines() if "Widget(" in line]


class TestRoute:
    def test_a_question_is_an_inline_answer_with_at_most_four_widgets(self):
        state = run("report", MockRelevanceChecker(), reports(10))
        assert len(state["ids"]) == INLINE_LIMIT
        assert "Board(" not in state["program"]

    def test_builder_makes_a_board_of_up_to_fifteen_widgets(self):
        state = run("@builder report", MockRelevanceChecker(), reports(30))
        assert len(state["ids"]) == BOARD_LIMIT
        assert f'board = Board("Report", [' in state["program"]

    def test_builder_names_the_board_after_the_request(self):
        assert 'Board("Sales Overview",' in run("@builder sales overview", MockRelevanceChecker())["program"]

    def test_a_request_with_no_words_gets_the_default_board_name(self):
        assert board_name_from("   ") == "AI board"

    def test_a_long_request_gives_a_short_board_name(self):
        assert len(board_name_from("sales " * 20)) <= 30

    def test_the_checker_does_not_see_the_builder_tag(self):
        checker = MockRelevanceChecker()
        run("@Builder top customers", checker)
        assert {message for message, _ in checker.calls} == {"top customers"}


class TestVerifyLoop:
    def test_a_rejected_widget_is_skipped_and_the_next_is_tried(self):
        checker = MockRelevanceChecker({"w00": 0.1})
        state = run("report", checker, reports(3))
        assert state["ids"] == ["w01", "w02"]
        assert state["rejected"] == ["w00"]
        assert [entry_id for _, entry_id in checker.calls] == ["w00", "w01", "w02"]

    def test_the_threshold_itself_is_approved(self):
        assert run("report", MockRelevanceChecker({"w00": 0.35}), reports(1))["ids"] == ["w00"]

    def test_just_below_the_threshold_is_rejected(self):
        assert run("report", MockRelevanceChecker({"w00": 0.349}), reports(1))["ids"] == []

    def test_the_threshold_can_be_changed(self):
        assert run("report", MockRelevanceChecker({"w00": 0.5}), reports(1), threshold=0.6)["ids"] == []
        assert run("report", MockRelevanceChecker({"w00": 0.5}), reports(1), threshold=0.4)["ids"] == ["w00"]

    def test_no_widget_is_checked_twice(self):
        checker = MockRelevanceChecker(default=0.0)
        run("report", checker, reports(5))
        ids = [entry_id for _, entry_id in checker.calls]
        assert len(ids) == len(set(ids)) == 5

    def test_approved_widgets_keep_the_keyword_order(self):
        catalog = [CatalogEntry("a", "Sales", ""), CatalogEntry("b", "Sales sales report", ""), CatalogEntry("c", "Sales", "")]
        assert run("sales report", MockRelevanceChecker(), catalog)["ids"] == ["b", "a", "c"]

    def test_stops_asking_once_the_limit_is_reached(self):
        checker = MockRelevanceChecker()
        run("report", checker, reports(10))
        assert len(checker.calls) == INLINE_LIMIT

    def test_an_inline_answer_stops_after_the_check_budget(self):
        checker = MockRelevanceChecker(default=0.0)
        state = run("report", checker, reports(30))
        assert len(checker.calls) == INLINE_CHECKS
        assert state["ids"] == []

    def test_a_board_stops_after_its_larger_check_budget(self):
        checker = MockRelevanceChecker(default=0.0)
        run("@builder report", checker, reports(30))
        assert len(checker.calls) == BOARD_CHECKS

    def test_a_widget_found_after_several_rejections_is_still_approved(self):
        scores = {f"w{n:02d}": 0.0 for n in range(6)}
        assert run("report", MockRelevanceChecker(scores), reports(8))["ids"] == ["w06", "w07"]

    def test_nothing_proposed_means_nothing_is_checked(self):
        checker = MockRelevanceChecker()
        state = run("weather in paris", checker)
        assert checker.calls == [] and state["ids"] == []


class TestUnchecked:
    def test_without_a_checker_the_keyword_candidates_are_used(self):
        state = run("report", None, reports(10))
        assert len(state["ids"]) == INLINE_LIMIT and state["unchecked"] is True and state["checks"] == 0

    def test_a_checker_that_is_down_from_the_start_falls_back_to_the_keywords(self):
        state = run("report", MockRelevanceChecker(fail_from=0), reports(10))
        assert state["ids"] == ["w00", "w01", "w02", "w03"]
        assert state["unchecked"] is True

    def test_a_checker_that_goes_down_midway_keeps_the_checked_results(self):
        state = run("report", MockRelevanceChecker({"w00": 0.0}, fail_from=2), reports(10))
        assert state["rejected"] == ["w00"]
        assert state["ids"] == ["w01", "w02", "w03", "w04"]
        assert state["checks"] == 2

    def test_unchecked_boards_are_not_limited_by_the_check_budget(self):
        assert len(run("@builder report", None, reports(30))["ids"]) == BOARD_LIMIT

    def test_the_answer_is_still_a_valid_program(self):
        assert run("report", MockRelevanceChecker(fail_from=0), reports(3))["program"].startswith("root = Stack(")


class TestReply:
    def test_the_sentence_is_built_from_catalog_titles(self):
        program = run("sales", MockRelevanceChecker({"sales-month": 0.0, "top-customers": 0.0}), DEFAULT_ENTRIES)["program"]
        assert 'Text("Here is Sales today, Day sales and Top materials.")' in program

    def test_four_titles_read_as_a_list(self):
        assert "Here is Sales today, Sales this month, Day sales and Top customers." in run("sales", MockRelevanceChecker(), DEFAULT_ENTRIES)["program"]

    def test_nothing_approved_says_so_with_no_widgets(self):
        program = run("report", MockRelevanceChecker(default=0.0), reports(3))["program"]
        assert program.splitlines() == ["root = Stack([intro])", 'intro = Text("I could not find a matching widget.")']

    def test_a_board_sentence_counts_its_widgets(self):
        assert "I built Report with 1 widget." in run("@builder report", MockRelevanceChecker(), reports(1))["program"]

    def test_every_program_has_a_root_and_only_catalog_ids(self):
        for message in ["sales", "weather", "@builder customers"]:
            program = run(message, MockRelevanceChecker(), DEFAULT_ENTRIES)["program"]
            assert program.startswith("root = Stack(")
            assert set(widget_ids(program)) <= {entry.id for entry in DEFAULT_ENTRIES}

    def test_a_title_with_quotes_cannot_break_the_program(self):
        catalog = [CatalogEntry("a", 'Sales "x")\nroot = Evil()', "")]
        program = run("sales", MockRelevanceChecker(), catalog)["program"]
        assert len(program.splitlines()) == 3 and "root = Evil()" not in program.splitlines()


class TestMatcher:
    def test_uses_the_matcher_it_is_given(self):
        catalog = [CatalogEntry("top-materials", "Top materials", "")]
        plan = PlanChat(MockRelevanceChecker(), KeywordMatcher({"top-materials": ["products"]}))
        assert plan.choose("which products", catalog) == ["top-materials"]


class TestReplyWriter:
    def run(self, writer, message="top customers", catalog=DEFAULT_ENTRIES):
        return PlanChat(MockRelevanceChecker(), reply_writer=writer).run(message, catalog)["program"]

    def test_a_clean_sentence_from_the_writer_is_used(self):
        assert 'Text("Showing the top customers for you.")' in self.run(MockReplyWriter("Showing the top customers for you."))

    def test_the_writer_gets_the_message_and_the_approved_titles(self):
        writer = MockReplyWriter("Showing the top customers for you.")
        self.run(writer)
        assert writer.calls == [("top customers", ["Top customers", "Top materials"], None)]

    def test_for_a_board_the_writer_also_gets_the_board_name_and_no_builder_tag(self):
        writer = MockReplyWriter("Your Top Customers board is ready: top customers.")
        program = self.run(writer, "@builder top customers")
        assert writer.calls == [("top customers", ["Top customers", "Top materials"], "Top Customers")]
        assert 'Text("Your Top Customers board is ready: top customers.")' in program

    @pytest.mark.parametrize("text", ["", "Okay I am ready!", "Showing top customers\nplus more lines", "Showing <b>top customers</b> now.", "Showing the top 5 customers now."])
    def test_a_sentence_that_fails_the_checks_is_replaced_by_the_code_sentence(self, text):
        assert 'Text("Here is Top customers and Top materials.")' in self.run(MockReplyWriter(text))

    def test_a_writer_that_is_down_falls_back_to_the_code_sentence(self):
        assert 'Text("Here is Top customers and Top materials.")' in self.run(MockReplyWriter(error=ReplyUnavailable()))

    def test_without_a_writer_the_code_sentence_is_used(self):
        assert 'Text("Here is Top customers and Top materials.")' in self.run(None)

    def test_nothing_found_never_asks_the_writer(self):
        writer = MockReplyWriter()
        program = self.run(writer, "weather in paris")
        assert writer.calls == [] and "I could not find a matching widget." in program

    def test_a_quote_in_the_writers_sentence_cannot_break_the_program(self):
        program = self.run(MockReplyWriter('Showing the "top customers") root = Evil() now.'))
        assert len(program.splitlines()) == 4 and "root = Evil()" not in program.splitlines()
