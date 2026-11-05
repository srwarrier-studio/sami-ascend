import json

import pytest
from conftest import make_client

from butterfly.infrastructure.api.standard.edmx import PRODUCT_METADATA, SPECS
from butterfly.infrastructure.api.standard.product import ROOT

SAMPLES = SPECS / "api_product"


def sample_row(name: str) -> dict:
    return json.loads((SAMPLES / name).read_text())["value"][0]


REAL_PRODUCT = sample_row("list-top3.json")
REAL_PLANT = sample_row("plants-of-products-top3.json")
REAL_UNIT = sample_row("units-top3.json")
REAL_DESCRIPTION = sample_row("descriptions-top3.json")


@pytest.fixture(scope="module")
def client():
    return make_client()


def get(client, path):
    return client.get(f"{ROOT}/{path}")


def kind(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "bool"
    if isinstance(value, (int, float)):
        return "number"
    return type(value).__name__


def mismatched(actual: dict, real: dict) -> list[str]:
    return [name for name in real if real[name] is not None and actual[name] is not None and kind(actual[name]) != kind(real[name])]


class TestTheRealMetadata:
    def test_is_the_saved_real_document(self, client):
        assert get(client, "$metadata").content == PRODUCT_METADATA.read_bytes()


class TestRows:
    @pytest.mark.parametrize(
        "path, real",
        [
            ("Product?$top=1", REAL_PRODUCT),
            ("ProductDescription?$top=1", REAL_DESCRIPTION),
            ("ProductPlant?$top=1", REAL_PLANT),
            ("ProductUnitOfMeasure?$top=1", REAL_UNIT),
        ],
    )
    def test_has_exactly_the_properties_and_types_of_the_real_row(self, client, path, real):
        row = get(client, path).json()["value"][0]
        assert list(row) == list(real)
        assert mismatched(row, real) == []

    def test_a_product_carries_the_materials_values(self, client):
        row = get(client, "Product('RM-1001')").json()
        assert (row["Product"], row["ProductType"], row["ProductGroup"], row["BaseUnit"], row["BaseISOUnit"]) == ("RM-1001", "FERT", "EXTRACT", "KG", "KGM")
        assert row["@odata.context"] == "$metadata#Product/$entity"

    def test_a_raw_material_is_type_roh(self, client):
        assert get(client, "Product('RAW-2001')").json()["ProductType"] == "ROH"

    def test_the_description_is_in_english(self, client):
        row = get(client, "ProductDescription(Product='RM-1001',Language='EN')").json()
        assert row["ProductDescription"] == "Curcumin extract 95%"

    def test_a_material_is_held_in_the_plants_of_its_company_only(self, client):
        rows = get(client, "ProductPlant?$filter=Product eq 'RM-1001'").json()["value"]
        assert [r["Plant"] for r in rows] == ["1000"]
        assert get(client, "ProductPlant(Product='RM-1001',Plant='2000')").status_code == 404

    def test_the_base_unit_is_the_only_unit_of_a_material(self, client):
        rows = get(client, "ProductUnitOfMeasure?$filter=Product eq 'RM-1001'").json()["value"]
        assert [(r["AlternativeUnit"], r["QuantityNumerator"], r["QuantityDenominator"]) for r in rows] == [("KG", 1, 1)]


class TestSearching:
    def test_by_the_start_of_the_number(self, client):
        rows = get(client, "Product?$filter=startswith(Product,'RAW-20')&$select=Product,BaseUnit").json()["value"]
        assert rows and all(r["Product"].startswith("RAW-20") for r in rows) and list(rows[0]) == ["@odata.etag", "Product", "BaseUnit"]

    def test_by_a_word_of_the_description_on_the_description_set(self, client):
        body = get(client, "ProductDescription?$filter=contains(ProductDescription,'Turmeric')&$count=true").json()
        assert body["@odata.count"] == len(body["value"]) > 0
        assert all("Turmeric" in r["ProductDescription"] for r in body["value"])

    def test_by_a_word_of_the_description_through_the_lambda_on_product(self, client):
        body = get(client, "Product?$filter=_ProductDescription/any(d:contains(d/ProductDescription,'Turmeric'))&$select=Product&$expand=_ProductDescription").json()
        assert body["value"]
        assert all("Turmeric" in row["_ProductDescription"][0]["ProductDescription"] for row in body["value"])
        assert body["@odata.context"] == "$metadata#Product(Product,_ProductDescription())"

    def test_the_lambda_can_be_combined_with_another_condition(self, client):
        rows = get(client, "Product?$filter=ProductType eq 'ROH' and _ProductDescription/any(d:contains(d/ProductDescription,'Turmeric'))&$select=Product,ProductType").json()["value"]
        assert rows and all(r["ProductType"] == "ROH" for r in rows)

    def test_pages_and_counts(self, client):
        body = get(client, "Product?$top=2&$skip=2&$count=true&$select=Product&$orderby=Product").json()
        assert len(body["value"]) == 2 and body["@odata.count"] > 4

    def test_count_segment_is_plain_text(self, client):
        response = get(client, "Product/$count?$filter=ProductType eq 'ROH'")
        assert response.text.isdigit() and response.headers["content-type"].startswith("text/plain")


class TestExpanding:
    def test_the_description_and_plants_and_units_of_a_product(self, client):
        for nav, key in [("_ProductDescription", "ProductDescription"), ("_ProductPlant", "Plant"), ("_ProductUnitOfMeasure", "AlternativeUnit")]:
            body = get(client, f"Product('RM-1001')?$expand={nav}").json()
            assert len(body[nav]) == 1 and key in body[nav][0]

    def test_a_navigation_path_lists_the_children(self, client):
        rows = get(client, "Product('RM-1001')/_ProductPlant").json()["value"]
        assert [r["Plant"] for r in rows] == ["1000"]

    def test_the_other_entity_sets_answer_empty(self, client):
        assert get(client, "ProductValuation").json()["value"] == []


def real_error(name: str) -> dict:
    return json.loads((SAMPLES / f"{name}.json").read_text())["error"]


class TestRefusalsLikeTheSandbox:
    @pytest.mark.parametrize(
        "path, status, sample",
        [
            ("Product('ZZZ999')", 404, "error-not-found"),
            ("Product?$filter=Nope eq 1", 400, "error-bad-filter"),
        ],
    )
    def test_gives_the_status_code_and_message_of_the_sample(self, client, path, status, sample):
        response = get(client, path)
        error, real = response.json()["error"], real_error(sample)
        assert response.status_code == status
        assert (error["code"], error["message"], error["@SAP__common.ExceptionCategory"]) == (real["code"], real["message"], real["@SAP__common.ExceptionCategory"])
        assert error["innererror"]["ErrorDetails"]["@SAP__common.Application"] == real["innererror"]["ErrorDetails"]["@SAP__common.Application"]

    def test_a_wrong_expand_name_is_refused(self, client):
        assert get(client, "Product?$expand=_Nope").json()["error"]["code"].startswith("/IWCOR/CX_OD_EXPAND_ERROR")

    def test_an_unknown_select_is_refused(self, client):
        assert get(client, "Product?$select=Nope").status_code == 400

    def test_an_unknown_option_is_refused(self, client):
        assert get(client, "Product?$foo=1").status_code == 400
