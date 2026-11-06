import httpx
import pytest

pytest.importorskip("butterfly")
from test_butterfly_requisition_gateway import InProcessButterfly, Unreachable

from butterfly.application.alpha import external as ext
from butterfly.infrastructure.memory.companies import COMPANIES
from workspace_api.domain.errors import SapNotReached
from workspace_api.infrastructure.butterfly_master_data_gateway import ButterflyMasterDataGateway, any_of, literal
from workspace_api.infrastructure.settings import Settings

SETTINGS = Settings(
    sap_product_url="http://butterfly/sap/opu/odata4/sap/api_product/srvd_a2x/sap/product/0001/",
    sap_plant_url="http://butterfly/sap/opu/odata4/sap/api_plant_2/srvd_a2x/sap/plant/0001/",
    sap_partner_url="http://butterfly/sap/opu/odata/sap/API_BUSINESS_PARTNER/",
)
INA1 = COMPANIES[0]


def gateway(transport: httpx.BaseTransport | None = None) -> ButterflyMasterDataGateway:
    return ButterflyMasterDataGateway(SETTINGS, transport or InProcessButterfly())


class TestPlants:
    def test_lists_the_plants_asked_for_with_their_names(self):
        plants = gateway().plants(["1000", "3000"])
        assert [p.plant for p in plants] == ["1000", "3000"] and all(p.name for p in plants)

    def test_no_plants_means_none(self):
        assert gateway().plants([]) == []


class TestMaterials:
    def test_lists_the_materials_held_in_the_plant_with_unit_group_and_description(self):
        page = gateway().materials(None, ["1000"], 100, 0)
        sold = {m[0] for m in INA1.materials}
        raw = {m[0] for m in INA1.raw_materials}
        assert {m.material for m in page.materials} == sold | raw and page.total == len(sold | raw)
        first = next(m for m in page.materials if m.material == "RM-1001")
        assert (first.description, first.unit, first.iso_unit, first.material_group, first.material_type, first.plants) == ("Curcumin extract 95%", "KG", "KGM", "EXTRACT", "FERT", ["1000"])

    def test_never_shows_materials_of_other_plants(self):
        numbers = {m.material for m in gateway().materials(None, ["1000"], 100, 0).materials}
        assert not numbers & {m[0] for company in COMPANIES[1:] for m in company.materials}

    def test_finds_by_the_start_of_the_number(self):
        found = gateway().materials("RAW-20", ["1000"], 100, 0)
        assert found.total > 0 and all(m.material.startswith("RAW-20") for m in found.materials)

    def test_finds_by_a_word_of_the_description(self):
        found = gateway().materials("Turmeric", ["1000"], 100, 0)
        assert found.total > 0 and all("Turmeric" in m.description for m in found.materials)

    def test_a_search_with_a_quote_does_not_break_the_call(self):
        assert gateway().materials("O'Brien", ["1000"], 100, 0).total == 0

    def test_pages_in_number_order_with_the_total(self):
        first = gateway().materials(None, ["1000"], 3, 0)
        second = gateway().materials(None, ["1000"], 3, 3)
        numbers = [m.material for m in first.materials + second.materials]
        assert numbers == sorted(numbers) and len(set(numbers)) == 6 and first.total == second.total > 6

    def test_no_plants_means_none(self):
        assert gateway().materials(None, [], 10, 0).total == 0


class TestCustomersAndSuppliers:
    def test_customers_of_the_company_with_their_names(self):
        page = gateway().customers(None, ["INA1"], 100, 0)
        assert {p.number for p in page.partners} == {ext(c.customer_id) for c in INA1.customers} and page.total == len(INA1.customers)
        assert all(p.name and p.company_codes == ["INA1"] for p in page.partners)

    def test_customers_search_by_number_and_by_name(self):
        target = INA1.customers[0]
        by_start = gateway().customers(target.customer_id[:8], ["INA1"], 10, 0)
        assert ext(target.customer_id) in {p.number for p in by_start.partners}
        by_name = gateway().customers(target.name.split()[0], ["INA1"], 10, 0)
        assert ext(target.customer_id) in {p.number for p in by_name.partners}
        by_number = gateway().customers(target.customer_id, ["INA1"], 10, 0)
        assert [p.number for p in by_number.partners] == [ext(target.customer_id)]

    def test_customers_of_another_company_are_not_listed(self):
        mine = {p.number for p in gateway().customers(None, ["INA1"], 100, 0).partners}
        assert not mine & {ext(c.customer_id) for c in COMPANIES[1].customers}

    def test_suppliers_of_the_company(self):
        page = gateway().suppliers(None, ["INA2"], 100, 0)
        assert {(p.number, p.name) for p in page.partners} == {(ext(s), n) for s, n in COMPANIES[1].suppliers}

    def test_a_search_with_a_quote_does_not_break_the_call(self):
        assert gateway().suppliers("O'Brien", ["INA2"], 10, 0).total == 0

    def test_no_companies_means_none(self):
        assert gateway().customers(None, [], 10, 0).total == 0


class TestWhenButterflyIsDown:
    @pytest.mark.parametrize("call", ["plants", "materials", "customers", "suppliers"])
    def test_is_not_reached(self, call):
        service = gateway(Unreachable())
        arguments = {"plants": (["1000"],), "materials": (None, ["1000"], 10, 0), "customers": (None, ["INA1"], 10, 0), "suppliers": (None, ["INA1"], 10, 0)}[call]
        with pytest.raises(SapNotReached):
            getattr(service, call)(*arguments)


class TestFilterText:
    def test_quotes_are_doubled(self):
        assert literal("a'b") == "'a''b'"

    def test_values_are_joined_with_or(self):
        assert any_of("Plant", ["1", "2"]) == "Plant eq '1' or Plant eq '2'"
