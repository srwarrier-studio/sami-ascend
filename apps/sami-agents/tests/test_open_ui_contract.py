import json
import re

import pytest

from sami_agents.application.keyword_matcher import KeywordMatcher
from sami_agents.application.plan_chat import BOARD_LIMIT, INLINE_LIMIT, PlanChat
from sami_agents.domain.entities.catalog import CatalogEntry
from sami_agents.entrypoint.evaluate import EVALS, load_cases, load_catalog
from sami_agents.infrastructure.alias_book import load_aliases
from sami_agents.infrastructure.mock_catalog_source import DEFAULT_ENTRIES
from sami_agents.infrastructure.mock_relevance_checker import MockRelevanceChecker
from sami_agents.infrastructure.mock_reply_writer import MockReplyWriter

CATALOG = load_catalog(EVALS / "catalog.json")
IDS = {entry.id for entry in CATALOG}
STATEMENT = re.compile(r"^([a-z][a-z0-9]*) = (.+)$")
STRING = r'"(?:[^"\\]|\\.)*"'
STACK = re.compile(r"^Stack\(\[([a-z][a-z0-9]*(?:, [a-z][a-z0-9]*)*)\]\)$")
TEXT = re.compile(rf"^Text\(({STRING})\)$")
WIDGET = re.compile(rf"^Widget\(({STRING})\)$")
BOARD = re.compile(rf"^Board\(({STRING}), \[({STRING}(?:, {STRING})*)\]\)$")


def check_program(program: str, ids: set[str] | None = None) -> dict:
    statements: dict[str, str] = {}
    for line in program.split("\n"):
        match = STATEMENT.match(line)
        assert match, f"not a statement: {line!r}"
        assert match.group(1) not in statements, f"{match.group(1)} defined twice"
        statements[match.group(1)] = match.group(2)
    assert "root" in statements and STACK.match(statements["root"]), "root must be a Stack"
    referenced: set[str] = set()
    widgets: list[str] = []
    boards: list[list[str]] = []
    for name, value in statements.items():
        if stack := STACK.match(value):
            referenced |= set(stack.group(1).split(", "))
        elif TEXT.match(value):
            json.loads(TEXT.match(value).group(1))
        elif widget := WIDGET.match(value):
            widgets.append(json.loads(widget.group(1)))
        elif board := BOARD.match(value):
            json.loads(board.group(1))
            boards.append(json.loads("[" + board.group(2) + "]"))
        else:
            raise AssertionError(f"unknown statement: {name} = {value}")
    assert referenced <= set(statements), "a name is used but never defined"
    assert set(statements) - {"root"} <= referenced, "a name is defined but never used, OpenUI would drop it"
    known = IDS if ids is None else ids
    assert set(widgets) <= known and all(set(board_ids) <= known for board_ids in boards)
    return {"widgets": widgets, "boards": boards}


class TestGoldenPrograms:
    def test_a_question_with_two_widgets(self):
        program = PlanChat(MockRelevanceChecker()).execute("top customers", DEFAULT_ENTRIES)
        assert program == "\n".join(
            [
                "root = Stack([intro, w1, w2])",
                'intro = Text("Here is Top customers and Top materials.")',
                'w1 = Widget("top-customers")',
                'w2 = Widget("top-materials")',
            ]
        )

    def test_a_builder_request(self):
        program = PlanChat(MockRelevanceChecker()).execute("@builder top customers", DEFAULT_ENTRIES)
        assert program == "\n".join(
            [
                "root = Stack([intro, board])",
                'intro = Text("I built Top Customers with 2 widgets.")',
                'board = Board("Top Customers", ["top-customers", "top-materials"])',
            ]
        )

    def test_nothing_found(self):
        assert PlanChat(MockRelevanceChecker()).execute("weather in paris", DEFAULT_ENTRIES) == "\n".join(
            ["root = Stack([intro])", 'intro = Text("I could not find a matching widget.")']
        )


class TestEveryProgramIsValid:
    @pytest.mark.parametrize("name", ["prompts.json", "heldout.json"])
    def test_every_evaluation_prompt_gives_a_valid_program(self, name):
        plan = PlanChat(MockRelevanceChecker(), KeywordMatcher(load_aliases()))
        for case in load_cases(EVALS / name):
            found = check_program(plan.execute(case.message, CATALOG))
            limit = BOARD_LIMIT if case.message.startswith("@builder") else INLINE_LIMIT
            assert len(found["widgets"]) <= INLINE_LIMIT and all(len(ids) <= limit for ids in found["boards"]), case.message

    @pytest.mark.parametrize("checker", [None, MockRelevanceChecker(default=0.0), MockRelevanceChecker(fail_from=0)])
    def test_whatever_the_checker_does_the_program_is_valid(self, checker):
        for message in ["sales", "@builder sales overview", "weather in paris", "@builder"]:
            check_program(PlanChat(checker).execute(message, CATALOG))

    @pytest.mark.parametrize("sentence", ['Showing the "top customers") root = Evil() now.', "Showing top customers\\ now please.", "Showing the top customers for you."])
    def test_whatever_the_sentence_writer_returns_the_program_is_valid(self, sentence):
        program = PlanChat(MockRelevanceChecker(), reply_writer=MockReplyWriter(sentence)).execute("top customers", DEFAULT_ENTRIES)
        assert check_program(program, {entry.id for entry in DEFAULT_ENTRIES})["widgets"] == ["top-customers", "top-materials"]

    def test_odd_titles_and_names_stay_inside_their_strings(self):
        catalog = [CatalogEntry("a-1", 'Sales "x")\n\\ root = Evil()', "")]
        check_program(PlanChat(MockRelevanceChecker()).execute("sales", catalog), {"a-1"})
        check_program(PlanChat(MockRelevanceChecker()).execute('@builder sales "x") root', catalog), {"a-1"})

    def test_non_ascii_text_is_kept_readable(self):
        catalog = [CatalogEntry("a", "Sales in ₹", "")]
        program = PlanChat(MockRelevanceChecker()).execute("sales", catalog)
        assert "₹" in program
        check_program(program, {"a"})


class TestTheValidatorItself:
    @pytest.mark.parametrize(
        "program",
        [
            'root = Stack([intro])\nintro = Text("a")\nextra = Text("b")',
            'root = Stack([intro, missing])\nintro = Text("a")',
            'intro = Text("a")',
            'root = Stack([intro])\nintro = Text("a"\nb")',
            'root = Stack([w1])\nw1 = Widget("not-a-widget")',
            'root = Text("a")',
            'root = Stack([intro])\nintro = Evil("a")',
        ],
    )
    def test_rejects_programs_openui_would_not_render_properly(self, program):
        with pytest.raises(AssertionError):
            check_program(program)
