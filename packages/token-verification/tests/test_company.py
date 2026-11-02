import pytest

from token_verification import Company


class TestCompanyCodes:
    def test_each_company_has_its_sap_company_code(self):
        assert [c.code for c in Company] == ["INA1", "INA2", "INA3"]

    def test_the_codes_are_all_different(self):
        assert len({c.code for c in Company}) == len(Company)

    @pytest.mark.parametrize("company", list(Company))
    def test_a_code_finds_its_company(self, company):
        assert Company.from_code(company.code) is company

    @pytest.mark.parametrize("code", ["", "INA4", "ina1", "sabinsa"])
    def test_an_unknown_code_is_refused(self, code):
        with pytest.raises(ValueError):
            Company.from_code(code)
