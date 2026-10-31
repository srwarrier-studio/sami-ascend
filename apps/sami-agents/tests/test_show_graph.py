import re

from sami_agents.application.show_graph import show_mermaid, show_text
from sami_agents.infrastructure.graph_loader import load_graph
from sami_agents.infrastructure.settings import GRAPH_FILE

GRAPH = load_graph(GRAPH_FILE)


class TestText:
    def test_every_node_is_listed_with_its_source_and_tests(self):
        text = show_text(GRAPH)
        for name in GRAPH.nodes:
            assert name in text
        assert "metric:sales.customer" in text and "record:production_order" in text
        assert "later_than, sum_changed" in text and "passthrough" in text

    def test_every_edge_is_listed_with_its_join_and_what_it_carries(self):
        text = show_text(GRAPH)
        for name in GRAPH.edges:
            assert name in text
        assert "Contract -> Customer   join Contract.SoldToParty = Customer.key   carries coverage_gap   shows -   lookback 60d" in text


class TestMermaid:
    def test_it_is_a_left_to_right_graph_with_one_line_per_node_and_edge(self):
        lines = show_mermaid(GRAPH).splitlines()
        assert lines[0] == "graph LR"
        assert len(lines) == 1 + len(GRAPH.nodes) + len(GRAPH.edges)

    def test_metric_nodes_are_rounded_and_edges_name_what_they_carry(self):
        text = show_mermaid(GRAPH)
        assert 'Customer(["Customer"])' in text and 'Contract["Contract"]' in text
        assert 'Contract -->|"coverage_gap"| Customer' in text
        assert 'Component -->|"link"| PurchaseDelivery' in text

    def test_ids_are_plain_words(self):
        for line in show_mermaid(GRAPH).splitlines()[1:]:
            assert re.match(r"^  \w+(\(\[|\[| -->)", line), line
