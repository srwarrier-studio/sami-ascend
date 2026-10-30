import json

from sami_agents.application.open_ui_writer import OpenUiWriter

writer = OpenUiWriter()


class TestAnswer:
    def test_writes_a_root_stack_with_a_text_and_one_widget_per_id(self):
        assert writer.answer("Here is Sales today.", ["sales-today", "top-customers"]) == "\n".join(
            [
                "root = Stack([intro, w1, w2])",
                'intro = Text("Here is Sales today.")',
                'w1 = Widget("sales-today")',
                'w2 = Widget("top-customers")',
            ]
        )

    def test_with_no_widgets_the_root_holds_only_the_text(self):
        assert writer.answer("Nothing.", []).splitlines() == ["root = Stack([intro])", 'intro = Text("Nothing.")']


class TestBoard:
    def test_writes_a_board_with_its_name_and_ids(self):
        assert writer.board("I built Sales.", "Sales", ["sales-today", "day-sales"]) == "\n".join(
            [
                "root = Stack([intro, board])",
                'intro = Text("I built Sales.")',
                'board = Board("Sales", ["sales-today", "day-sales"])',
            ]
        )


class TestEscaping:
    def test_quotes_backslashes_and_line_breaks_stay_inside_the_string(self):
        program = writer.answer('He said "hi"\nnext \\ line', [])
        assert len(program.splitlines()) == 2
        text = program.splitlines()[1].removeprefix("intro = Text(").removesuffix(")")
        assert json.loads(text) == 'He said "hi"\nnext \\ line'

    def test_a_board_name_with_a_quote_cannot_close_the_string(self):
        program = writer.board("ok", 'My "board")\nroot = Evil()', ["a"])
        assert len(program.splitlines()) == 3
        assert program.splitlines()[0] == "root = Stack([intro, board])"

    def test_keeps_non_ascii_text_readable(self):
        assert "₹" in writer.answer("Sales in ₹", [])
