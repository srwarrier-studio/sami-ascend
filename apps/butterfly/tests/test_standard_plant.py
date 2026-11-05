import json

import pytest
from conftest import make_client

from butterfly.domain.entities.master_data import PLANT_COMPANIES, SALES_ORGANIZATIONS
from butterfly.infrastructure.api.standard.edmx import PLANT_METADATA, SPECS
from butterfly.infrastructure.api.standard.plant import ROOT

SAMPLES = SPECS / "api_plant_2"
REAL_ROW = json.loads((SAMPLES / "list-top3.json").read_text())["value"][0]


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


class TestTheRealMetadata:
    def test_is_the_saved_real_document(self, client):
        assert get(client, "$metadata").content == PLANT_METADATA.read_bytes()


class TestRows:
    def test_has_exactly_the_properties_and_types_of_the_real_row(self, client):
        row = get(client, "Plant?$top=1").json()["value"][0]
        assert list(row) == list(REAL_ROW)
        assert "@odata.etag" not in row
        assert [n for n in REAL_ROW if REAL_ROW[n] is not None and row[n] is not None and kind(row[n]) != kind(REAL_ROW[n])] == []

    def test_every_plant_of_the_company_table_is_listed(self, client):
        body = get(client, "Plant?$count=true&$orderby=Plant").json()
        assert [r["Plant"] for r in body["value"]] == sorted(PLANT_COMPANIES) and body["@odata.count"] == len(PLANT_COMPANIES)

    def test_a_plant_carries_its_organizations(self, client):
        row = get(client, "Plant('1000')").json()
        assert (row["PlantName"], row["ValuationArea"], row["SalesOrganization"], row["Language"]) == (row["PlantName"], "1000", SALES_ORGANIZATIONS["INA1"], "EN") and row["PlantName"].endswith(" plant")
        assert row["DefaultPurchasingOrganization"] and row["@odata.context"] == "$metadata#Plant/$entity"

    def test_select_adds_the_key_to_the_context(self, client):
        body = get(client, "Plant?$select=PlantName&$top=1").json()
        assert body["@odata.context"] == "$metadata#Plant(PlantName,Plant)" and list(body["value"][0]) == ["Plant", "PlantName"]

    def test_filters_and_counts(self, client):
        assert get(client, "Plant?$filter=Plant eq '2000'&$select=Plant").json()["value"][0]["Plant"] == "2000"
        assert get(client, "Plant/$count").text == str(len(PLANT_COMPANIES))


def real_error(name: str) -> dict:
    return json.loads((SAMPLES / f"{name}.json").read_text())["error"]


class TestRefusalsLikeTheSandbox:
    @pytest.mark.parametrize("path, status, sample", [("Plant('NOPE')", 404, "error-not-found"), ("Plant?$filter=Nope eq 1", 400, "error-bad-filter")])
    def test_gives_the_status_code_and_message_of_the_sample(self, client, path, status, sample):
        response = get(client, path)
        error, real = response.json()["error"], real_error(sample)
        assert response.status_code == status
        assert (error["code"], error["message"], error["@SAP__common.ExceptionCategory"]) == (real["code"], real["message"], real["@SAP__common.ExceptionCategory"])
        assert error["innererror"]["ErrorDetails"]["@SAP__common.Application"] == real["innererror"]["ErrorDetails"]["@SAP__common.Application"]

    def test_a_plant_has_nothing_to_expand(self, client):
        for path in ("Plant?$expand=_Nope", "Plant('1000')?$expand=_Nope"):
            assert get(client, path).json()["error"]["code"].startswith("/IWCOR/CX_OD_EXPAND_ERROR")

    def test_an_unknown_select_and_option_are_refused(self, client):
        assert get(client, "Plant?$select=Nope").status_code == 400
        assert get(client, "Plant?$foo=1").status_code == 400
