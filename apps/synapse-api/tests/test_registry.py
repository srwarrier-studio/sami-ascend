from pathlib import Path

import pytest

from synapse_api.infrastructure.registry_loader import RegistryError, load_registry
from synapse_api.infrastructure.settings import REGISTRY_PATH

GOOD = """
[metric.sales]
label = "Sales"
service = "sales"
measure = "TotalNetAmount"
date = "OrderDate"
currency = "Currency"
by.day = { entity = "SalesSummaryByDay", order = "OrderDate,Currency" }
by.customer = { entity = "SalesSummaryByCustomer", key = "SoldToParty", name = "CustomerName", order = "OrderDate" }

[record.contract]
service = "drivers"
entity = "SalesContract"
key_fields = ["SoldToParty"]
order = "ValidFrom"
"""


def load(tmp_path: Path, text: str):
    path = tmp_path / "registry.toml"
    path.write_text(text)
    return load_registry(path)


def fails(tmp_path: Path, text: str, mention: str):
    with pytest.raises(RegistryError) as error:
        load(tmp_path, text)
    assert mention in str(error.value)


class TestTheShippedFile:
    REGISTRY = load_registry(REGISTRY_PATH)

    def test_it_holds_sales_and_the_four_record_types(self):
        assert list(self.REGISTRY.metrics) == ["sales"]
        assert list(self.REGISTRY.records) == ["contract", "purchase_delivery", "production_order", "production_component"]

    def test_sales_has_day_customer_and_material_and_only_material_has_a_quantity(self):
        sales = self.REGISTRY.metrics["sales"]
        assert list(sales.dimensions) == ["day", "customer", "material"]
        assert [d.name for d in sales.dimensions.values() if d.quantity] == ["material"]
        assert sales.dimensions["customer"].key == "SoldToParty"

    def test_intervals_and_delays_are_where_the_contract_has_dates(self):
        records = self.REGISTRY.records
        assert records["contract"].interval.end == "ValidTo" and records["contract"].delay is None
        assert records["purchase_delivery"].interval.fallback == "PromisedDeliveryDate"
        assert records["purchase_delivery"].interval.open_to_today
        assert records["production_order"].delay.due == "PlannedEndDate"
        assert records["production_component"].interval is None


class TestLoading:
    def test_a_minimal_file_loads(self, tmp_path):
        registry = load(tmp_path, GOOD)
        assert registry.metrics["sales"].dimensions["customer"].name_field == "CustomerName"
        assert registry.records["contract"].key_fields == ("SoldToParty",)

    def test_an_interval_without_a_fallback_falls_back_to_its_end(self, tmp_path):
        registry = load(tmp_path, GOOD + 'interval = { from = "ValidFrom", to = "ValidTo" }\n')
        assert registry.records["contract"].interval.fallback == "ValidTo"


class TestEveryBadEntryNamesItself:
    def test_a_missing_field(self, tmp_path):
        fails(tmp_path, GOOD.replace('measure = "TotalNetAmount"\n', ""), "metric 'sales' needs 'measure'")

    def test_an_unknown_service(self, tmp_path):
        fails(tmp_path, GOOD.replace('service = "sales"', 'service = "crm"'), "metric 'sales' has unknown service 'crm'")

    def test_a_record_with_an_unknown_service(self, tmp_path):
        fails(tmp_path, GOOD.replace('service = "drivers"', 'service = "crm"'), "record 'contract' has unknown service")

    def test_a_dimension_without_a_key(self, tmp_path):
        fails(tmp_path, GOOD.replace('key = "SoldToParty", ', ""), "dimension 'customer' needs 'key' and 'name'")

    def test_a_metric_without_a_day_entity(self, tmp_path):
        fails(tmp_path, GOOD.replace('by.day = { entity = "SalesSummaryByDay", order = "OrderDate,Currency" }\n', ""), "needs a 'by.day'")

    def test_an_interval_field_that_is_not_text(self, tmp_path):
        fails(tmp_path, GOOD + 'interval = { from = 5, to = "ValidTo" }\n', "record 'contract' interval needs 'from' as text")

    def test_open_to_today_must_be_true_or_false(self, tmp_path):
        fails(tmp_path, GOOD + 'interval = { from = "A", to = "B", open_to_today = "yes" }\n', "open_to_today")

    def test_key_fields_must_be_a_list_of_text(self, tmp_path):
        fails(tmp_path, GOOD.replace('["SoldToParty"]', '"SoldToParty"'), "'key_fields' as a list")
        fails(tmp_path, GOOD.replace('["SoldToParty"]', "[]"), "'key_fields' as a list")

    def test_a_misspelt_key_is_not_ignored(self, tmp_path):
        fails(tmp_path, GOOD.replace('label = "Sales"', 'label = "Sales"\nlable = "x"'), "unknown key 'lable'")

    def test_a_duplicate_name_is_refused(self, tmp_path):
        fails(tmp_path, GOOD + '\n[record.contract]\nservice = "drivers"\n', "registry registry.toml")

    def test_an_unknown_section(self, tmp_path):
        fails(tmp_path, GOOD + "\n[graph.x]\na = 1\n", "unknown section graph")

    def test_a_missing_file(self, tmp_path):
        with pytest.raises(RegistryError):
            load_registry(tmp_path / "nope.toml")
