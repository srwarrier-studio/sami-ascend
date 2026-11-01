import pytest

from intent_api.domain.errors import LibraryError
from intent_api.infrastructure.domain_loader import SCENARIOS_FILE, load_domains


def library(tmp_path, text):
    path = tmp_path / "scenarios.toml"
    path.write_text(text)
    return path


class TestLoadDomains:
    def test_reads_each_domain_description(self, tmp_path):
        path = library(tmp_path, '[domain.Sales]\ndescription = " sales orders "\n[domain.Purchase]\ndescription = "spend"\n')
        assert load_domains(path) == {"Sales": "sales orders", "Purchase": "spend"}

    @pytest.mark.parametrize("text", ["[domain.Sales]\n", '[domain.Sales]\ndescription = ""\n', "[domain.Sales]\ndescription = 3\n", "domain = 1\n"])
    def test_a_domain_without_a_description_is_rejected(self, tmp_path, text):
        with pytest.raises(LibraryError, match="Sales|domain"):
            load_domains(library(tmp_path, text))

    def test_a_library_without_domains_is_rejected(self, tmp_path):
        with pytest.raises(LibraryError, match="no domains"):
            load_domains(library(tmp_path, ""))

    def test_a_missing_or_broken_file_is_rejected(self, tmp_path):
        with pytest.raises(LibraryError):
            load_domains(tmp_path / "absent.toml")
        with pytest.raises(LibraryError):
            load_domains(library(tmp_path, "[domain"))

    def test_the_shipped_file_has_the_six_domains(self):
        assert list(load_domains(SCENARIOS_FILE)) == ["Sales", "Purchase", "Shipments", "Finance", "Inventory", "Production"]
