from pathlib import Path

import pytest

from sami_agents.application.check_graph import CheckGraph
from sami_agents.infrastructure.graph_loader import load_graph
from sami_agents.infrastructure.registry_info_loader import load_contract_fields, load_registry_info
from sami_agents.infrastructure.settings import CONTRACTS_FOLDER, GRAPH_FILE, REGISTRY_FILE

REGISTRY = load_registry_info(REGISTRY_FILE)
CONTRACTS = load_contract_fields(CONTRACTS_FOLDER)

BASE = """
[node.Customer]
source = "metric:sales.customer"

[node.Contract]
source = "record:contract"
anomaly = { kind = "coverage_gap", from = "ValidFrom", to = "ValidTo" }

[edge.customer_contracts]
cause = "Contract"
effect = "Customer"
join = { cause = "SoldToParty", effect = "key" }
carries = ["coverage_gap"]
"""


def check(tmp_path: Path, text: str):
    path = tmp_path / "graph.toml"
    path.write_text(text)
    return CheckGraph(REGISTRY, CONTRACTS).execute(load_graph(path))


def problems(tmp_path, text):
    return check(tmp_path, text)[0]


class TestTheInputs:
    def test_the_registry_and_contracts_are_read_from_the_repository(self):
        assert list(REGISTRY.metrics["sales"]) and "customer" in REGISTRY.metrics["sales"]
        assert REGISTRY.records["purchase_delivery"].key_fields == ("Material", "Supplier", "PurchaseOrder")
        assert "ActualDeliveryDate" in CONTRACTS["PurchaseDelivery"] and "ProductionOrder" in CONTRACTS["ProductionOrderComponent"]


class TestTheShippedGraph:
    def test_it_passes_the_check_with_no_problems(self):
        found, _ = CheckGraph(REGISTRY, CONTRACTS).execute(load_graph(GRAPH_FILE))
        assert found == []

    def test_the_two_supply_and_demand_loops_are_listed_as_information(self):
        _, info = CheckGraph(REGISTRY, CONTRACTS).execute(load_graph(GRAPH_FILE))
        assert info and all(line.startswith("info: ") for line in info)


class TestEachProblemIsReportedByName:
    def test_a_minimal_graph_is_fine(self, tmp_path):
        assert problems(tmp_path, BASE) == []

    def test_a_record_type_that_is_not_in_the_registry(self, tmp_path):
        assert "node 'Contract': record type 'deal' is not in the registry" in problems(tmp_path, BASE.replace("record:contract", "record:deal"))

    def test_a_metric_that_is_not_in_the_registry(self, tmp_path):
        assert "node 'Customer': metric 'weather' is not in the registry" in problems(tmp_path, BASE.replace("sales.customer", "weather.customer"))

    def test_a_dimension_the_metric_does_not_have_or_the_day_dimension(self, tmp_path):
        assert any("no dimension 'region'" in p for p in problems(tmp_path, BASE.replace("sales.customer", "sales.region")))
        assert any("no dimension 'day'" in p for p in problems(tmp_path, BASE.replace("sales.customer", "sales.day")))

    def test_a_field_the_contract_does_not_list(self, tmp_path):
        found = problems(tmp_path, BASE.replace('to = "ValidTo"', 'to = "ValidUntil"'))
        assert "node 'Contract': anomaly 'coverage_gap' uses field 'ValidUntil' that SalesContract does not have in the contract" in found

    def test_a_join_field_that_is_not_a_key_field(self, tmp_path):
        found = problems(tmp_path, BASE.replace('cause = "SoldToParty"', 'cause = "ContractStatus"'))
        assert any("edge 'customer_contracts': join field 'ContractStatus' is not a key field of record type 'contract'" in p for p in found)

    def test_a_metric_side_must_join_on_key(self, tmp_path):
        found = problems(tmp_path, BASE.replace('effect = "key"', 'effect = "SoldToParty"'))
        assert any("metric node 'Customer', its join field must be 'key'" in p for p in found)

    def test_carries_a_kind_the_cause_does_not_define(self, tmp_path):
        assert "edge 'customer_contracts': carries 'later_than' but its cause 'Contract' has no such anomaly" in problems(tmp_path, BASE.replace('["coverage_gap"]', '["later_than"]'))

    def test_shows_a_kind_the_effect_does_not_define(self, tmp_path):
        assert "edge 'customer_contracts': shows 'value_changed' but its effect 'Customer' has no such anomaly" in problems(tmp_path, BASE + 'shows = ["value_changed"]\n')

    def test_shows_on_a_passthrough_effect(self, tmp_path):
        text = BASE.replace('source = "metric:sales.customer"', 'source = "record:production_component"\npassthrough = true').replace('effect = "key"', 'effect = "ProductionOrder"')
        found = problems(tmp_path, text + 'shows = ["later_than"]\n')
        assert any("shows ['later_than'] but its effect 'Customer' is passthrough" in p for p in found)

    def test_an_id_field_the_contract_does_not_list_and_an_id_on_a_metric_node(self, tmp_path):
        assert any("id field 'Nope' is not in SalesContract" in p for p in problems(tmp_path, BASE.replace('source = "record:contract"', 'source = "record:contract"\nid = "Nope"')))
        assert any("a metric node has no rows" in p for p in problems(tmp_path, BASE.replace('source = "metric:sales.customer"', 'source = "metric:sales.customer"\nid = "SoldToParty"')))

    def test_the_new_kind_checks_its_fields_against_the_contract(self, tmp_path):
        text = BASE.replace('anomaly = { kind = "coverage_gap", from = "ValidFrom", to = "ValidTo" }', 'anomaly = { kind = "set_changed", field = "Nope", date = "ValidFrom" }').replace('["coverage_gap"]', '["set_changed"]')
        assert any("uses field 'Nope' that SalesContract does not have" in p for p in problems(tmp_path, text))

    def test_the_reason_field_is_checked_too(self, tmp_path):
        text = BASE.replace('anomaly = { kind = "coverage_gap", from = "ValidFrom", to = "ValidTo" }', 'anomaly = { kind = "later_than", due = "ValidFrom", done = "ValidTo", reason = "Nope" }').replace('["coverage_gap"]', '["later_than"]')
        assert any("uses field 'Nope'" in p for p in problems(tmp_path, text))

    def test_a_record_kind_on_a_metric_node_and_the_reverse(self, tmp_path):
        on_metric = BASE.replace('source = "metric:sales.customer"', 'source = "metric:sales.customer"\nanomaly = { kind = "later_than", due = "a", done = "b" }')
        assert any("node 'Customer': anomaly 'later_than' needs rows" in p for p in problems(tmp_path, on_metric))
        on_record = BASE.replace('anomaly = { kind = "coverage_gap", from = "ValidFrom", to = "ValidTo" }', 'anomaly = { kind = "value_changed", min_percent = 5 }')
        assert any("node 'Contract': anomaly 'value_changed' needs a metric" in p for p in problems(tmp_path, on_record))

    def test_a_passthrough_node_with_anomalies_or_a_carried_kind(self, tmp_path):
        both = BASE.replace('source = "record:contract"', 'source = "record:contract"\npassthrough = true')
        found = problems(tmp_path, both)
        assert "node 'Contract': is passthrough and also has anomalies" in found
        assert any("its cause 'Contract' is passthrough" in p for p in found)

    def test_a_node_no_edge_touches(self, tmp_path):
        assert "node 'Lonely': no edge touches it" in problems(tmp_path, BASE + '\n[node.Lonely]\nsource = "record:contract"\n')

    def test_an_entity_missing_from_every_contract(self, tmp_path):
        registry = REGISTRY
        path = tmp_path / "graph.toml"
        path.write_text(BASE)
        found, _ = CheckGraph(registry, {}).execute(load_graph(path))
        assert "node 'Contract': entity 'SalesContract' is in no contract under docs/sap" in found

    def test_several_problems_all_come_in_one_run(self, tmp_path):
        text = BASE.replace("record:contract", "record:deal") + '\n[node.Lonely]\nsource = "record:contract"\n'
        assert len(problems(tmp_path, text)) >= 2


class TestLoops:
    def test_two_edges_in_opposite_directions_make_a_loop_that_is_only_information(self, tmp_path):
        text = BASE + """
[edge.back]
cause = "Customer"
effect = "Contract"
join = { cause = "key", effect = "SoldToParty" }
"""
        found, info = check(tmp_path, text)
        assert found == [] or all("loop" not in p for p in found)
        assert info == ["info: Contract, Customer form a loop; walks stop at their limits"]

    def test_a_graph_without_a_loop_has_no_information(self, tmp_path):
        assert check(tmp_path, BASE)[1] == []
