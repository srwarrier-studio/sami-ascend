import json

import pytest

from intent_api.domain.errors import LibraryError
from intent_api.infrastructure.eval_loader import QUESTIONS_FILE, load_cases
from intent_api.infrastructure.library_loader import load_library

LIBRARY = load_library()


def row(**fields):
    base = {"id": "q1", "question": "sales in august", "part": "single", "domain": "Sales", "scenarios": ["sales_value"], "heldout": False}
    base.update(fields)
    return base


def cases_of(tmp_path, rows):
    path = tmp_path / "questions.json"
    path.write_text(json.dumps(rows))
    return load_cases(LIBRARY, path)


def problems(tmp_path, rows) -> str:
    with pytest.raises(LibraryError) as error:
        cases_of(tmp_path, rows)
    return str(error.value)


class TestLoadCases:
    def test_reads_a_case(self, tmp_path):
        case = cases_of(tmp_path, [row()])[0]
        assert (case.id, case.domain, case.scenarios, case.heldout, case.should_answer) == ("q1", "Sales", frozenset({"sales_value"}), False, True)

    def test_a_refuse_case_has_no_scenarios_and_may_name_other(self, tmp_path):
        case = cases_of(tmp_path, [row(part="refuse", domain="Other", scenarios=[])])[0]
        assert not case.should_answer

    @pytest.mark.parametrize("fields, text", [
        ({"id": ""}, "unique id"), ({"question": " "}, "needs a question"), ({"part": "double"}, "part must be"),
        ({"domain": "Nowhere"}, "unknown domain"), ({"scenarios": ["missing"]}, "known scenario ids"),
        ({"scenarios": []}, "only 'refuse' questions have no scenarios"), ({"part": "refuse"}, "only 'refuse' questions have no scenarios"),
        ({"heldout": "no"}, "heldout must be"),
    ])
    def test_a_bad_case_is_rejected_with_its_number(self, tmp_path, fields, text):
        message = problems(tmp_path, [row(**fields)])
        assert "question #1" in message and text in message

    def test_a_duplicate_id_is_rejected(self, tmp_path):
        assert "unique id" in problems(tmp_path, [row(), row()])

    def test_a_missing_file_is_rejected(self, tmp_path):
        with pytest.raises(LibraryError):
            load_cases(LIBRARY, tmp_path / "absent.json")


class TestShippedQuestions:
    def test_load_against_the_shipped_library_with_a_held_out_part(self):
        cases = load_cases(LIBRARY, QUESTIONS_FILE)
        held = [case for case in cases if case.heldout]
        assert len(cases) > 100 and len(cases) - len(held) >= 50 and 0.2 < len(held) / len(cases) < 0.7
        assert {case.part for case in cases} == {"single", "multi", "refuse"}
