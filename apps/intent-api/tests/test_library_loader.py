import pytest

from intent_api.domain.errors import LibraryError
from intent_api.infrastructure.library_loader import SCENARIOS_FILE, load_domains, load_library

DOMAINS = '[domain.Sales]\ndescription = "sales"\n[domain.Purchase]\ndescription = "spend"\n'


def scenario(**fields) -> str:
    body = {"id": '"sales_value"', "domain": '"Sales"', "description": '"the sales figure"', "examples": '["sales in July"]', "needs": '["period"]', "covers": "[]"}
    body.update({key: value for key, value in fields.items() if value is not None})
    for key in [key for key, value in fields.items() if value is None]:
        del body[key]
    return "[[scenario]]\n" + "".join(f"{key} = {value}\n" for key, value in body.items())


def library(tmp_path, text):
    path = tmp_path / "scenarios.toml"
    path.write_text(text)
    return path


def rejected(tmp_path, text) -> str:
    with pytest.raises(LibraryError) as error:
        load_library(library(tmp_path, text))
    return str(error.value)


class TestDomains:
    def test_reads_each_domain_description(self, tmp_path):
        path = library(tmp_path, '[domain.Sales]\ndescription = " sales orders "\n[domain.Purchase]\ndescription = "spend"\n')
        assert load_domains(path) == {"Sales": "sales orders", "Purchase": "spend"}

    @pytest.mark.parametrize("text", ["[domain.Sales]\n", '[domain.Sales]\ndescription = ""\n', "[domain.Sales]\ndescription = 3\n"])
    def test_a_domain_without_a_description_is_rejected(self, tmp_path, text):
        assert "domain 'Sales': needs a description" in rejected(tmp_path, text)

    def test_a_library_without_domains_is_rejected(self, tmp_path):
        assert "no domains" in rejected(tmp_path, "")

    def test_domain_must_be_a_table(self, tmp_path):
        assert "'domain' must be a table" in rejected(tmp_path, "domain = 1\n")

    def test_a_missing_or_broken_file_is_rejected(self, tmp_path):
        with pytest.raises(LibraryError):
            load_library(tmp_path / "absent.toml")
        assert "scenarios.toml" in rejected(tmp_path, "[domain")

    def test_an_unknown_section_is_rejected(self, tmp_path):
        assert "unknown section 'slot'" in rejected(tmp_path, DOMAINS + "[slot]\n")


class TestScenarios:
    def test_reads_a_scenario(self, tmp_path):
        loaded = load_library(library(tmp_path, DOMAINS + scenario(needs='["period", "top"]'))).scenarios["sales_value"]
        assert (loaded.domain, loaded.description, loaded.examples, loaded.needs, loaded.covers) == ("Sales", "the sales figure", ("sales in July",), ("period", "top"), ())

    def test_needs_and_covers_are_optional(self, tmp_path):
        loaded = load_library(library(tmp_path, DOMAINS + scenario(needs=None, covers=None))).scenarios["sales_value"]
        assert (loaded.needs, loaded.covers) == ((), ())

    def test_a_duplicate_id_is_rejected(self, tmp_path):
        assert "scenario 'sales_value': duplicate id" in rejected(tmp_path, DOMAINS + scenario() + scenario())

    def test_an_unknown_domain_is_rejected(self, tmp_path):
        assert "unknown domain 'Shipments'" in rejected(tmp_path, DOMAINS + scenario(domain='"Shipments"'))

    def test_an_unknown_slot_is_rejected(self, tmp_path):
        assert "unknown slot 'month'" in rejected(tmp_path, DOMAINS + scenario(needs='["month"]'))

    @pytest.mark.parametrize("examples", [None, "[]", '[""]', '"sales in July"'])
    def test_a_scenario_without_examples_is_rejected(self, tmp_path, examples):
        assert "needs at least one example" in rejected(tmp_path, DOMAINS + scenario(examples=examples))

    @pytest.mark.parametrize("description", [None, '""', "3"])
    def test_a_scenario_without_a_description_is_rejected(self, tmp_path, description):
        assert "needs a description" in rejected(tmp_path, DOMAINS + scenario(description=description))

    def test_a_scenario_without_an_id_is_rejected(self, tmp_path):
        assert "scenario #1: needs an id" in rejected(tmp_path, DOMAINS + scenario(id=None))

    def test_an_unknown_key_is_rejected(self, tmp_path):
        assert "unknown key 'words'" in rejected(tmp_path, DOMAINS + scenario(words='["sales"]'))

    def test_scenario_must_be_a_list_of_tables(self, tmp_path):
        assert "'scenario' must be a list" in rejected(tmp_path, DOMAINS + "[scenario.sales_value]\ndomain = 1\n")

    def test_every_problem_is_reported_together(self, tmp_path):
        message = rejected(tmp_path, DOMAINS + scenario(domain='"Nowhere"', needs='["month"]'))
        assert "unknown domain" in message and "unknown slot" in message


class TestCovers:
    def test_covering_an_unknown_scenario_is_rejected(self, tmp_path):
        assert "covers unknown scenario 'missing'" in rejected(tmp_path, DOMAINS + scenario(covers='["missing"]'))

    def test_covering_itself_is_a_loop(self, tmp_path):
        assert "covers loops back" in rejected(tmp_path, DOMAINS + scenario(covers='["sales_value"]'))

    def test_covering_in_a_circle_is_a_loop(self, tmp_path):
        text = DOMAINS + scenario(id='"a"', covers='["b"]') + scenario(id='"b"', covers='["c"]') + scenario(id='"c"', covers='["a"]')
        message = rejected(tmp_path, text)
        assert all(f"scenario '{name}': covers loops back" in message for name in "abc")

    def test_covering_a_chain_is_fine(self, tmp_path):
        text = DOMAINS + scenario(id='"a"', covers='["b"]') + scenario(id='"b"', covers='["c"]') + scenario(id='"c"')
        assert load_library(library(tmp_path, text)).scenarios["a"].covers == ("b",)


class TestShippedFile:
    def test_has_the_six_domains(self):
        assert list(load_domains(SCENARIOS_FILE)) == ["Sales", "Purchase", "Shipments", "Finance", "Inventory", "Production"]

    def test_passes_the_checks_and_has_the_fourteen_draft_scenarios(self):
        scenarios = load_library(SCENARIOS_FILE).scenarios
        assert len(scenarios) == 14 and {scenario.domain for scenario in scenarios.values()} == {"Sales", "Purchase"}
