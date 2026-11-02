from pathlib import Path

import pytest

from intent_api.domain.errors import GraphError
from intent_api.infrastructure.graph_loader import load_graph

SHIPPED = Path(__file__).resolve().parents[1] / "graph.toml"

GOOD = """
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


def load(tmp_path, text):
    path = tmp_path / "graph.toml"
    path.write_text(text)
    return load_graph(path)


def problems_of(tmp_path, text):
    with pytest.raises(GraphError) as error:
        load(tmp_path, text)
    return error.value.problems


class TestTheShippedGraph:
    GRAPH = load_graph(SHIPPED)

    def test_it_has_the_nodes_and_edges_for_sales_production_and_supply(self):
        assert list(self.GRAPH.nodes) == ["Customer", "Product", "PurchasedMaterial", "Contract", "ProductionOrder", "Component", "PurchaseDelivery"]
        assert len(self.GRAPH.edges) == 8

    def test_sources_dimensions_and_passthrough_are_read(self):
        nodes = self.GRAPH.nodes
        assert (nodes["Customer"].source_kind, nodes["Customer"].source, nodes["Customer"].dimension) == ("metric", "sales", "customer")
        assert (nodes["Contract"].source_kind, nodes["Contract"].source) == ("record", "contract")
        assert nodes["Component"].passthrough and not nodes["Component"].anomalies

    def test_several_anomalies_with_defaults_filled_in(self):
        late, changed = self.GRAPH.nodes["ProductionOrder"].anomalies
        assert (late.kind, late.params["min_days"]) == ("later_than", 3)
        assert (changed.kind, changed.params["pad_days"], changed.params["min_percent"]) == ("sum_changed", 30, 10)

    def test_two_edges_join_the_same_nodes_in_opposite_directions(self):
        pairs = {(e.cause, e.effect): e for e in self.GRAPH.edges.values()}
        assert pairs[("Component", "ProductionOrder")].carries == ()
        assert pairs[("ProductionOrder", "Component")].carries == ("sum_changed",)
        assert pairs[("PurchaseDelivery", "Component")].carries == ("later_than",)
        assert pairs[("Component", "PurchaseDelivery")].carries == ()

    def test_ids_and_reasons_and_the_new_kind_are_read(self):
        nodes = self.GRAPH.nodes
        assert (nodes["Contract"].id, nodes["ProductionOrder"].id, nodes["PurchaseDelivery"].id, nodes["Customer"].id) == ("SalesContract", "ProductionOrder", "PurchaseOrder", None)
        assert nodes["ProductionOrder"].anomalies[0].params["reason"] == "DelayReason"
        assert [a.kind for a in nodes["PurchaseDelivery"].anomalies] == ["later_than", "sum_changed", "set_changed"]
        assert nodes["PurchaseDelivery"].anomalies[2].params["pad_days"] == 30

    def test_nodes_have_readable_labels(self):
        nodes = self.GRAPH.nodes
        assert (nodes["ProductionOrder"].label, nodes["PurchasedMaterial"].label, nodes["Contract"].label) == ("production order", "purchased material", "contract")

    def test_edges_say_what_they_show_at_the_effect(self):
        edges = self.GRAPH.edges
        assert edges["production_for_product"].shows == ("value_changed",)
        assert edges["sales_drive_production"].shows == ("sum_changed",)
        assert edges["customer_contracts"].shows == ()

    def test_lookback_defaults_to_sixty_days(self):
        assert all(e.lookback_days == 60 for e in self.GRAPH.edges.values())


class TestLoading:
    def test_a_minimal_file_loads(self, tmp_path):
        graph = load(tmp_path, GOOD)
        edge = graph.edges["customer_contracts"]
        assert (edge.cause, edge.effect, edge.cause_field, edge.effect_field, edge.carries) == ("Contract", "Customer", "SoldToParty", "key", ("coverage_gap",))

    def test_a_single_anomaly_table_and_a_list_both_work(self, tmp_path):
        text = GOOD.replace('anomaly = { kind = "coverage_gap", from = "ValidFrom", to = "ValidTo" }', 'anomaly = [{ kind = "coverage_gap", from = "ValidFrom", to = "ValidTo" }]')
        assert len(load(tmp_path, text).nodes["Contract"].anomalies) == 1

    def test_lookback_can_be_set(self, tmp_path):
        assert load(tmp_path, GOOD + "lookback_days = 90\n").edges["customer_contracts"].lookback_days == 90


class TestEveryProblemNamesItself:
    def test_a_source_that_is_not_record_or_metric(self, tmp_path):
        assert "node 'Customer': 'source' must look like" in problems_of(tmp_path, GOOD.replace("metric:sales.customer", "sales"))[0]

    def test_a_metric_source_without_a_dimension(self, tmp_path):
        assert "metric:sales" in problems_of(tmp_path, GOOD.replace("metric:sales.customer", "metric:sales"))[0]

    def test_an_unknown_anomaly_kind(self, tmp_path):
        found = problems_of(tmp_path, GOOD.replace("coverage_gap\", from", "gone_quiet\", from"))
        assert any("node 'Contract': anomaly kind must be one of" in p and "gone_quiet" in p for p in found)

    def test_a_missing_parameter(self, tmp_path):
        found = problems_of(tmp_path, GOOD.replace(', to = "ValidTo"', ""))
        assert "node 'Contract' anomaly 'coverage_gap': needs 'to' as text" in found

    def test_a_missing_threshold(self, tmp_path):
        text = GOOD.replace('anomaly = { kind = "coverage_gap", from = "ValidFrom", to = "ValidTo" }', 'anomaly = { kind = "sum_changed", field = "F", date = "D" }')
        assert "node 'Contract' anomaly 'sum_changed': needs 'min_percent' as a number" in problems_of(tmp_path, text)

    def test_a_threshold_that_is_not_a_number(self, tmp_path):
        text = GOOD.replace('anomaly = { kind = "coverage_gap", from = "ValidFrom", to = "ValidTo" }', 'anomaly = { kind = "value_changed", min_percent = "ten" }')
        assert any("'min_percent' must be a number" in p for p in problems_of(tmp_path, text))

    def test_an_unknown_parameter(self, tmp_path):
        found = problems_of(tmp_path, GOOD.replace('to = "ValidTo"', 'to = "ValidTo", sloppy = 1'))
        assert "node 'Contract' anomaly 'coverage_gap': unknown parameter 'sloppy'" in found

    def test_an_edge_to_a_node_that_does_not_exist(self, tmp_path):
        assert "edge 'customer_contracts': unknown node 'Client'" in problems_of(tmp_path, GOOD.replace('effect = "Customer"', 'effect = "Client"'))

    def test_a_join_without_both_sides(self, tmp_path):
        found = problems_of(tmp_path, GOOD.replace('join = { cause = "SoldToParty", effect = "key" }', 'join = { cause = "SoldToParty" }'))
        assert "edge 'customer_contracts': 'join' needs 'cause' and 'effect' field names as text" in found

    def test_carries_must_be_a_list_and_lookback_a_whole_number(self, tmp_path):
        assert any("'carries' must be a list" in p for p in problems_of(tmp_path, GOOD.replace('["coverage_gap"]', '"coverage_gap"')))
        assert any("'lookback_days' must be a whole number" in p for p in problems_of(tmp_path, GOOD + "lookback_days = -1\n"))

    def test_an_id_must_be_text_and_a_reason_must_be_text(self, tmp_path):
        assert any("'id' must be a field name" in p for p in problems_of(tmp_path, GOOD.replace('source = "record:contract"', 'source = "record:contract"\nid = 5')))
        assert any("'reason' must be text" in p for p in problems_of(tmp_path, GOOD.replace('anomaly = { kind = "coverage_gap", from = "ValidFrom", to = "ValidTo" }', 'anomaly = { kind = "later_than", due = "a", done = "b", reason = 3 }')))

    def test_a_label_must_be_text(self, tmp_path):
        assert any("'label' must be text" in p for p in problems_of(tmp_path, GOOD.replace('source = "record:contract"', 'source = "record:contract"\nlabel = 4')))

    def test_set_changed_needs_its_fields(self, tmp_path):
        text = GOOD.replace('anomaly = { kind = "coverage_gap", from = "ValidFrom", to = "ValidTo" }', 'anomaly = { kind = "set_changed", field = "Supplier" }')
        assert "node 'Contract' anomaly 'set_changed': needs 'date' as text" in problems_of(tmp_path, text)

    def test_shows_must_be_a_list(self, tmp_path):
        assert any("'shows' must be a list" in p for p in problems_of(tmp_path, GOOD + 'shows = "value_changed"\n'))

    def test_a_misspelt_key_is_not_ignored(self, tmp_path):
        assert any("unknown key 'pasthrough'" in p for p in problems_of(tmp_path, GOOD.replace('source = "metric:sales.customer"', 'source = "metric:sales.customer"\npasthrough = true')))

    def test_an_unknown_section(self, tmp_path):
        assert "graph: unknown section 'rules'" in problems_of(tmp_path, GOOD + "\n[rules.x]\na = 1\n")

    def test_a_duplicate_node_is_a_syntax_error_that_names_the_file(self, tmp_path):
        assert "graph.toml" in problems_of(tmp_path, GOOD + '\n[node.Customer]\nsource = "record:x"\n')[0]

    def test_every_problem_is_reported_in_one_go(self, tmp_path):
        text = GOOD.replace("metric:sales.customer", "sales").replace('effect = "Customer"', 'effect = "Client"')
        assert len(problems_of(tmp_path, text)) >= 2

    def test_a_missing_file(self, tmp_path):
        with pytest.raises(GraphError):
            load_graph(tmp_path / "nope.toml")
