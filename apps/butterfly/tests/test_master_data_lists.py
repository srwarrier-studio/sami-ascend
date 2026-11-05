import pytest

from butterfly.domain.entities.master_data import PLANT_COMPANIES
from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.in_memory_master_data_repo import InMemoryMasterDataRepo
from butterfly.infrastructure.sqlite.master_data_repo import SqliteMasterDataRepo


@pytest.fixture(params=["memory", "sqlite"])
def repo(request):
    return InMemoryMasterDataRepo() if request.param == "memory" else SqliteMasterDataRepo()


class TestCustomers:
    def test_lists_every_customer_with_its_company(self, repo):
        listed = {(c.customer_id, c.company_code) for c in repo.list_customers()}
        assert listed == {(c.customer_id, company.code) for company in COMPANIES for c in company.customers}


class TestProducts:
    def test_lists_the_sold_and_the_raw_materials_of_every_company(self, repo):
        products = repo.list_products()
        expected = sum(len(c.materials) + len(c.raw_materials) for c in COMPANIES)
        assert len(products) == expected and len({p.material_id for p in products}) == expected

    def test_a_sold_material_is_finished_and_a_raw_material_is_raw(self, repo):
        by_id = {p.material_id: p for p in repo.list_products()}
        assert by_id["RM-1001"].material_type == "FERT" and by_id["RAW-2001"].material_type == "ROH"

    def test_a_product_has_its_description_unit_group_and_company(self, repo):
        turmeric = next(p for p in repo.list_products() if p.material_id == "RAW-2001")
        assert (turmeric.description, turmeric.unit, turmeric.material_group, turmeric.company_code) == ("Turmeric rhizome, dried", "KG", "BOTANIC", "INA1")
        assert turmeric.iso_unit == "KGM"

    def test_every_product_has_a_material_group(self, repo):
        assert [p.material_id for p in repo.list_products() if not p.material_group] == []

    def test_raw_materials_cannot_be_sold(self, repo):
        assert repo.get_material("RAW-2001") is None and repo.get_material("RM-1001") is not None


class TestSuppliers:
    def test_lists_every_supplier_with_its_company(self, repo):
        listed = {(s.supplier_id, s.name, s.company_code) for s in repo.list_suppliers()}
        assert listed == {(sid, name, company.code) for company in COMPANIES for sid, name in company.suppliers}


class TestPlants:
    def test_every_company_has_a_plant_and_every_plant_a_known_company(self):
        assert set(PLANT_COMPANIES.values()) == {company.code for company in COMPANIES}
