import pytest

from intent_api.application.describe_answers import DescribeAnswers
from intent_api.domain.entities.scenario import Library, Scenario
from intent_api.domain.errors import LibraryError
from intent_api.infrastructure.answers_loader import ANSWERS_FILE, load_answers
from intent_api.infrastructure.library_loader import load_library

LIBRARY = Library(
    {"Sales": "sales"},
    {name: Scenario(name, "Sales", "text", ("example",)) for name in ("sales_value", "sales_compare", "sales_trend", "sales_top")},
)


def entry(**fields) -> str:
    body = {"scenario": '"sales_value"', "response": '"value"', "metric": '"sales"'}
    body.update({key: value for key, value in fields.items() if value is not None})
    for key in [key for key, value in fields.items() if value is None]:
        del body[key]
    return "[[answer]]\n" + "".join(f"{key} = {value}\n" for key, value in body.items())


def answers(tmp_path, text):
    path = tmp_path / "answers.toml"
    path.write_text(text)
    return path


def rejected(tmp_path, text) -> str:
    with pytest.raises(LibraryError) as error:
        load_answers(LIBRARY, answers(tmp_path, text))
    return str(error.value)


class TestReadingEntries:
    def test_reads_each_kind_of_response(self, tmp_path):
        text = (
            entry()
            + entry(scenario='"sales_compare"', response='"compare"', against='"last_year"')
            + entry(scenario='"sales_trend"', response='"trend"')
            + entry(scenario='"sales_top"', response='"ranking"', by='"customer"')
        )
        rules = load_answers(LIBRARY, answers(tmp_path, text))
        assert rules["sales_value"].response == "value"
        assert rules["sales_compare"].against == "last_year"
        assert rules["sales_trend"].metric == "sales"
        assert rules["sales_top"].by == "customer"

    def test_an_empty_file_has_no_answers(self, tmp_path):
        assert load_answers(LIBRARY, answers(tmp_path, "")) == {}

    def test_the_summary_counts_the_answers(self, tmp_path):
        rules = load_answers(LIBRARY, answers(tmp_path, entry()))
        assert DescribeAnswers(rules).summary() == "ok: 1 answers"


class TestRejectedEntries:
    def test_an_unknown_scenario(self, tmp_path):
        assert "unknown scenario 'nope'" in rejected(tmp_path, entry(scenario='"nope"'))

    def test_an_unknown_response(self, tmp_path):
        assert "unknown response 'chart'" in rejected(tmp_path, entry(response='"chart"'))

    def test_a_ranking_without_by(self, tmp_path):
        assert "a ranking needs 'by'" in rejected(tmp_path, entry(scenario='"sales_top"', response='"ranking"'))

    def test_a_compare_without_against(self, tmp_path):
        assert "a compare needs 'against'" in rejected(tmp_path, entry(scenario='"sales_compare"', response='"compare"'))

    def test_by_on_a_value(self, tmp_path):
        assert "only a ranking has 'by'" in rejected(tmp_path, entry(by='"customer"'))

    def test_against_on_a_value(self, tmp_path):
        assert "only a compare has 'against'" in rejected(tmp_path, entry(against='"previous"'))

    def test_a_missing_metric(self, tmp_path):
        assert "needs a metric" in rejected(tmp_path, entry(metric=None))

    def test_an_unknown_key(self, tmp_path):
        assert "unknown key 'color'" in rejected(tmp_path, entry(color='"red"'))

    def test_a_duplicate_scenario(self, tmp_path):
        assert "duplicate scenario" in rejected(tmp_path, entry() + entry())

    def test_an_unknown_section(self, tmp_path):
        assert "unknown section 'extra'" in rejected(tmp_path, "[extra]\na = 1\n")

    def test_a_file_that_is_not_toml(self, tmp_path):
        assert "answers answers.toml" in rejected(tmp_path, "[[answer")

    def test_all_problems_are_reported_together(self, tmp_path):
        message = rejected(tmp_path, entry(scenario='"nope"') + entry(response='"chart"'))
        assert "unknown scenario" in message and "unknown response" in message


class TestTheShippedFile:
    def test_every_answer_belongs_to_a_scenario_of_the_library(self):
        rules = load_answers(load_library())
        assert len(rules) == 14
        assert (rules["sales_why"].response, rules["purchases_why"].metric) == ("why", "purchases")
