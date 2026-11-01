import pytest

from intent_api.domain.errors import LibraryError
from intent_api.infrastructure.family_loader import FAMILIES_FILE, load_families
from intent_api.infrastructure.library_loader import load_library

LIBRARY = load_library()
SLOTS = '[slots]\nperiod = ["last month", "in May"]\n'


def family(**fields) -> str:
    body = {"id": '"sales_value_a"', "domain": '"Sales"', "scenario": '"sales_value"', "templates": '["sales {period}"]'}
    body.update(fields)
    return "[[family]]\n" + "".join(f"{key} = {value}\n" for key, value in body.items() if value is not None)


def loaded(tmp_path, text):
    path = tmp_path / "families.toml"
    path.write_text(text)
    return load_families(LIBRARY, path)


def rejected(tmp_path, text) -> str:
    with pytest.raises(LibraryError) as error:
        loaded(tmp_path, text)
    return str(error.value)


class TestLoadFamilies:
    def test_reads_a_family_with_its_slots(self, tmp_path):
        families, slots = loaded(tmp_path, SLOTS + family())
        assert slots == {"period": ["last month", "in May"]}
        assert (families[0].id, families[0].domain, families[0].scenario, families[0].nothing, families[0].templates) == ("sales_value_a", "Sales", "sales_value", False, ("sales {period}",))

    def test_a_refusal_family_has_no_scenario_and_other_is_a_domain(self, tmp_path):
        families, _ = loaded(tmp_path, SLOTS + family(id='"joke"', domain='"Other"', scenario=None, templates='["tell me a joke"]'))
        assert (families[0].domain, families[0].scenario) == ("Other", None)

    @pytest.mark.parametrize("fields, text", [
        ({"domain": '"Nowhere"'}, "unknown domain"),
        ({"scenario": '"missing"'}, "is not a scenario of domain"),
        ({"scenario": '"purchases_value"'}, "is not a scenario of domain"),
        ({"scenario": '"sales_value"', "nothing": "true"}, "cannot also be 'nothing'"),
        ({"templates": "[]"}, "needs a list of templates"),
        ({"templates": '["sales {month}"]'}, "unknown slot 'month'"),
        ({"id": '""'}, "needs an id"),
        ({"nothing": '"yes"'}, "must be true or false"),
    ])
    def test_a_bad_family_is_rejected(self, tmp_path, fields, text):
        assert text in rejected(tmp_path, SLOTS + family(**fields))

    def test_a_fragment_family_has_no_domain_item_and_needs_a_scenario(self, tmp_path):
        families, _ = loaded(tmp_path, SLOTS + family(domain_item="false"))
        assert families[0].domain_item is False
        assert "needs a scenario" in rejected(tmp_path, SLOTS + family(id='"joke"', domain='"Other"', scenario=None, domain_item="false"))
        assert "'domain_item' must be true or false" in rejected(tmp_path, SLOTS + family(domain_item='"no"'))

    def test_a_duplicate_id_is_rejected(self, tmp_path):
        assert "duplicate id" in rejected(tmp_path, SLOTS + family() + family())

    @pytest.mark.parametrize("slots", ["", "[slots]\n", "[slots]\nperiod = []\n", '[slots]\nperiod = [1]\n'])
    def test_slots_are_needed_and_must_be_text(self, tmp_path, slots):
        assert "slot" in rejected(tmp_path, slots + family())

    def test_a_missing_file_is_rejected(self, tmp_path):
        with pytest.raises(LibraryError):
            load_families(LIBRARY, tmp_path / "absent.toml")


class TestHeldOut:
    def test_every_fourth_family_of_a_group_is_held_out(self, tmp_path):
        text = SLOTS + "".join(family(id=f'"sales_value_{name}"') for name in "abcdefgh")
        held = {item.id for item in loaded(tmp_path, text)[0] if item.heldout}
        assert held == {"sales_value_d", "sales_value_h"}

    def test_groups_are_counted_separately(self, tmp_path):
        text = SLOTS + "".join(family(id=f'"a_{name}"') for name in "abc") + "".join(family(id=f'"b_{name}"', scenario='"sales_trend"') for name in "abcd")
        assert {item.id for item in loaded(tmp_path, text)[0] if item.heldout} == {"b_d"}


class TestShippedFamilies:
    def test_load_and_cover_every_scenario_and_domain_with_a_held_out_family(self):
        families, _ = load_families(LIBRARY, FAMILIES_FILE)
        assert {family.scenario for family in families if family.scenario} == set(LIBRARY.scenarios)
        for scenario in LIBRARY.scenarios:
            group = [family for family in families if family.scenario == scenario]
            assert len(group) >= 4 and any(family.heldout for family in group) and any(not family.heldout for family in group)
        assert {family.domain for family in families} == {*LIBRARY.domains, "Other"}
