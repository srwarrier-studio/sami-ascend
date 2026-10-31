from datetime import date
from decimal import Decimal

import pytest

from sami_agents.application import walk_graph
from sami_agents.application.walk_graph import MAX_DEPTH, MAX_VISITS, WalkGraph
from sami_agents.domain.entities.finding import MemberChange, Start, Window
from sami_agents.domain.errors import DataUnavailable
from sami_agents.infrastructure.graph_loader import load_graph
from sami_agents.infrastructure.mock_data_source import MockDataSource
from sami_agents.infrastructure.settings import GRAPH_FILE

TODAY = date(2026, 10, 31)
AUGUST = Window.before(date(2026, 8, 1), date(2026, 8, 31))
SHIPPED = load_graph(GRAPH_FILE)


def walk(source, mode, starts, graph=SHIPPED, window=AUGUST, token="tok"):
    return WalkGraph(graph, source).execute(mode, starts, window, token, TODAY)


def production(order, planned_end, actual_end, material="RM-1002", planned_start="2026-07-06", quantity="4000.000", reason=None):
    return {"ProductionOrder": order, "Material": material, "PlannedStartDate": planned_start, "PlannedEndDate": planned_end, "ActualEndDate": actual_end, "PlannedQuantity": quantity, "DelayReason": reason}


def delivery(order, promised, actual, material="RAW-2002", ordered="2026-06-24", quantity="5000.000"):
    return {"PurchaseOrder": order, "Material": material, "PromisedDeliveryDate": promised, "ActualDeliveryDate": actual, "OrderDate": ordered, "OrderedQuantity": quantity}


def component(order, material="RAW-2002"):
    return {"ProductionOrder": order, "Material": material}


SUPPLY = {
    "production_order": [production("0001000417", "2026-07-20", "2026-08-03", reason="MATERIAL_SHORTAGE"), production("0001000388", "2026-06-20", "2026-06-21", planned_start="2026-06-06")],
    "production_component": [component("0001000417"), component("0001000388")],
    "purchase_delivery": [delivery("4500001207", "2026-07-14", "2026-07-26"), delivery("4500001150", "2026-06-10", "2026-06-11")],
}


def names(path):
    return [(step.node, step.kind) for step in path]


class TestRootCauseThroughSupply:
    def result(self):
        return walk(MockDataSource(SUPPLY), "root_cause", [Start("Product", "RM-1002")])

    def test_it_finds_the_late_production_order_and_behind_it_the_late_delivery(self):
        [path] = self.result().paths
        assert names(path) == [("ProductionOrder", "later_than"), ("PurchaseDelivery", "later_than")]

    def test_each_step_carries_its_numbers_dates_and_the_rows_that_show_it(self):
        [order, late_delivery] = self.result().paths[0]
        assert (order.keys, order.numbers["days_late"], order.at, order.rows[0]["DelayReason"]) == (("RM-1002",), 14, date(2026, 7, 20), "MATERIAL_SHORTAGE")
        assert (late_delivery.keys, late_delivery.numbers["days_late"], late_delivery.at, late_delivery.rows[0]["PurchaseOrder"]) == (("RAW-2002",), 12, date(2026, 7, 14), "4500001207")

    def test_a_normal_delivery_is_never_reported(self):
        steps = [s for path in self.result().paths for s in path]
        assert "4500001150" not in {r["PurchaseOrder"] for s in steps for r in s.rows if "PurchaseOrder" in r}

    def test_the_component_link_is_walked_through_without_being_reported(self):
        assert "Component" not in {s.node for path in self.result().paths for s in path}

    def test_a_walk_with_nothing_unusual_gives_no_paths(self):
        calm = {**SUPPLY, "production_order": [production("O1", "2026-07-20", "2026-07-21")]}
        result = walk(MockDataSource(calm), "root_cause", [Start("Product", "RM-1002")])
        assert (result.paths, result.truncated) == ([], False)

    def test_a_late_order_with_on_time_deliveries_stops_at_the_order(self):
        on_time = {**SUPPLY, "purchase_delivery": [delivery("4500001150", "2026-07-14", "2026-07-15")]}
        [path] = walk(MockDataSource(on_time), "root_cause", [Start("Product", "RM-1002")]).paths
        assert names(path) == [("ProductionOrder", "later_than")]

    def test_a_cause_that_starts_after_its_effect_is_dropped(self):
        too_late = {**SUPPLY, "purchase_delivery": [delivery("P1", "2026-07-25", "2026-08-05")]}
        [path] = walk(MockDataSource(too_late), "root_cause", [Start("Product", "RM-1002")]).paths
        assert names(path) == [("ProductionOrder", "later_than")]

    def test_a_cause_that_starts_on_the_same_day_is_kept(self):
        same_day = {**SUPPLY, "purchase_delivery": [delivery("P1", "2026-07-20", "2026-08-05")]}
        [path] = walk(MockDataSource(same_day), "root_cause", [Start("Product", "RM-1002")]).paths
        assert len(path) == 2

    def test_events_outside_the_lookback_are_not_asked_for(self):
        source = MockDataSource(SUPPLY)
        walk(source, "root_cause", [Start("Product", "RM-1002")])
        first = next(c for c in source.calls if c[:2] == ("records", "production_order"))
        assert (first[4], first[5]) == (date(2026, 6, 2), date(2026, 8, 31))

    def test_every_call_carries_the_users_token(self):
        source = MockDataSource(SUPPLY)
        walk(source, "root_cause", [Start("Product", "RM-1002")], token="user-token")
        assert set(source.tokens) == {"user-token"}

    def test_several_starts_each_get_their_own_paths(self):
        source = MockDataSource({**SUPPLY, "production_order": SUPPLY["production_order"] + [production("0001000500", "2026-07-20", "2026-08-10", material="RM-1005", reason="MACHINE_BREAKDOWN")]})
        result = walk(source, "root_cause", [Start("Product", "RM-1002"), Start("Product", "RM-1005")])
        assert [path[0].keys for path in result.paths] == [("RM-1002",), ("RM-1005",)]


class TestRootCauseOnCustomers:
    def test_a_customer_without_a_valid_contract_in_the_window_has_a_coverage_gap(self):
        contract = {"SalesContract": "0040000127", "SoldToParty": "A", "ValidFrom": "2025-07-13", "ValidTo": "2026-07-12"}
        [path] = walk(MockDataSource({"contract": [contract]}), "root_cause", [Start("Customer", "A")]).paths
        [step] = path
        assert (step.node, step.kind, step.numbers["days_uncovered"], step.at) == ("Contract", "coverage_gap", 50, date(2026, 7, 13))

    def test_a_customer_whose_contract_covers_the_window_has_no_cause(self):
        contract = {"SalesContract": "C", "SoldToParty": "A", "ValidFrom": "2026-01-01", "ValidTo": "2026-12-31"}
        assert walk(MockDataSource({"contract": [contract]}), "root_cause", [Start("Customer", "A")]).paths == []


class TestEdgesCarryOnlyTheirKinds:
    GRAPH = """
[node.Sales]
source = "metric:sales.material"

[node.Order]
source = "record:production_order"
anomaly = [
  { kind = "later_than", due = "PlannedEndDate", done = "ActualEndDate" },
  { kind = "sum_changed", field = "PlannedQuantity", date = "PlannedStartDate", min_percent = 10 },
]

[edge.supply]
cause = "Order"
effect = "Sales"
join = { cause = "Material", effect = "key" }
carries = ["later_than"]
"""

    def graph(self, tmp_path, text=None):
        path = tmp_path / "g.toml"
        path.write_text(text or self.GRAPH)
        return load_graph(path)

    def test_only_the_carried_kind_is_tested(self, tmp_path):
        grew = [production("O1", "2026-07-20", "2026-07-21", planned_start="2026-07-06", quantity="5000.000"), production("O0", "2026-06-20", "2026-06-21", planned_start="2026-06-06", quantity="1000.000")]
        assert walk(MockDataSource({"production_order": grew}), "root_cause", [Start("Sales", "RM-1002")], self.graph(tmp_path)).paths == []

    def test_the_other_kind_is_found_when_the_edge_carries_it(self, tmp_path):
        grew = [production("O1", "2026-07-20", "2026-07-21", quantity="5000.000"), production("O0", "2026-06-20", "2026-06-21", planned_start="2026-06-06", quantity="1000.000")]
        graph = self.graph(tmp_path, self.GRAPH.replace('carries = ["later_than"]', 'carries = ["sum_changed"]'))
        [path] = walk(MockDataSource({"production_order": grew}), "root_cause", [Start("Sales", "RM-1002")], graph).paths
        assert names(path) == [("Order", "sum_changed")]


class TestRootCauseThroughDemand:
    DEMAND = {
        "purchase_delivery": [delivery("P1", "2026-08-14", "2026-08-15", ordered="2026-07-25", quantity="6750.000")],
        "production_component": [component("O1"), component("O2"), component("O3")],
        "production_order": [
            production("O1", "2026-06-20", "2026-06-20", planned_start="2026-05-10", quantity="4000.000"),
            production("O2", "2026-07-20", "2026-07-20", planned_start="2026-07-06", quantity="5400.000"),
            production("O3", "2026-08-20", "2026-08-20", planned_start="2026-08-05", quantity="5400.000"),
        ],
    }
    CHANGE = MemberChange(Decimal("121000.00"), Decimal("90000.00"), Decimal("34.44"))

    def result(self):
        source = MockDataSource(self.DEMAND, {("sales", "material", "RM-1002"): self.CHANGE})
        # components of RAW-2002 are the production orders O1..O3 whose product is RM-1002
        return walk(source, "root_cause", [Start("PurchaseDelivery", "RAW-2002", "Material")])

    def test_it_follows_extra_demand_from_purchases_through_components_and_production_to_sales(self):
        [path] = self.result().paths
        assert names(path) == [("ProductionOrder", "sum_changed"), ("Product", "value_changed")]

    def test_the_production_orders_are_judged_together_as_a_group(self):
        [order, _] = self.result().paths[0]
        assert order.keys == ("O1", "O2", "O3")
        assert order.numbers["change_percent"] > 10 and {r["ProductionOrder"] for r in order.rows} == {"O2", "O3"}

    def test_the_sales_step_has_the_members_change(self):
        [_, product] = self.result().paths[0]
        assert (product.keys, product.numbers["change_percent"]) == (("RM-1002",), Decimal("34.44"))

    def test_late_supply_is_not_mistaken_for_demand(self):
        assert all(s.kind != "later_than" for path in self.result().paths for s in path)


class TestImpact:
    def source(self, change=None):
        changes = {("sales", "material", "RM-1002"): change} if change else {}
        return MockDataSource(SUPPLY, changes)

    START = Start("PurchaseDelivery", "4500001207", "PurchaseOrder")

    def test_a_late_delivery_reaches_the_late_production_order_and_the_sales_that_fell(self):
        change = MemberChange(Decimal("60.00"), Decimal("100.00"), Decimal("-40.00"))
        [path] = walk(self.source(change), "impact", [self.START]).paths
        assert names(path) == [("PurchaseDelivery", "later_than"), ("ProductionOrder", "later_than"), ("Product", "value_changed")]

    def test_it_stops_at_production_when_sales_did_not_move(self):
        [path] = walk(self.source(MemberChange(Decimal("99.00"), Decimal("100.00"), Decimal("-1.00"))), "impact", [self.START]).paths
        assert names(path) == [("PurchaseDelivery", "later_than"), ("ProductionOrder", "later_than")]

    def test_a_start_with_nothing_unusual_gives_no_paths(self):
        assert walk(self.source(), "impact", [Start("PurchaseDelivery", "4500001150", "PurchaseOrder")]).paths == []

    def test_the_first_step_is_the_start_with_its_evidence(self):
        [path] = walk(self.source(), "impact", [self.START]).paths
        assert (path[0].edge, path[0].keys, path[0].numbers["days_late"]) == (None, ("4500001207",), 12)

    def test_a_production_effect_before_its_cause_is_dropped(self):
        early = {**SUPPLY, "production_order": [production("0001000417", "2026-07-10", "2026-07-28")]}
        [path] = walk(MockDataSource(early), "impact", [self.START]).paths
        assert names(path) == [("PurchaseDelivery", "later_than")]


class TestDependency:
    def result(self):
        source = MockDataSource(SUPPLY)
        return source, walk(source, "dependency", [Start("Product", "RM-1002")])

    def test_it_lists_the_related_nodes_and_keys_without_testing_anything(self):
        _, result = self.result()
        related = {(r.node, r.key) for r in result.related}
        assert ("ProductionOrder", "RM-1002") in related and ("Component", "0001000417") in related
        assert ("PurchaseDelivery", "RAW-2002") in related and result.paths == []

    def test_a_normal_delivery_is_counted_too(self):
        _, result = self.result()
        assert next(r for r in result.related if r.node == "PurchaseDelivery").rows == 2

    def test_it_reads_over_the_widest_window_the_api_allows(self):
        source, _ = self.result()
        first = next(c for c in source.calls if c[:2] == ("records", "production_order"))
        assert (first[5] - first[4]).days == 399 and first[5] == date(2026, 8, 31)


class TestLimitsAndLoops:
    CHAIN = "".join(
        f'[node.N{i}]\nsource = "record:t{i}"\nanomaly = {{ kind = "later_than", due = "due", done = "done" }}\n\n' for i in range(9)
    ) + "".join(
        f'[edge.e{i}]\ncause = "N{i + 1}"\neffect = "N{i}"\njoin = {{ cause = "k", effect = "k" }}\ncarries = ["later_than"]\n\n' for i in range(8)
    )
    ROW = {"k": "1", "due": "2026-07-01", "done": "2026-07-20"}

    def graph(self, tmp_path, text):
        path = tmp_path / "g.toml"
        path.write_text(text)
        return load_graph(path)

    def test_a_long_chain_stops_at_the_depth_limit_and_says_so(self, tmp_path):
        source = MockDataSource({f"t{i}": [self.ROW] for i in range(9)})
        result = walk(source, "root_cause", [Start("N0", "1", "k")], self.graph(tmp_path, self.CHAIN))
        assert result.truncated and max(len(p) for p in result.paths) == MAX_DEPTH

    def test_a_loop_in_the_graph_ends_and_no_node_repeats_on_a_path(self, tmp_path):
        text = self.CHAIN.split("[edge")[0] + '[edge.forward]\ncause = "N1"\neffect = "N0"\njoin = { cause = "k", effect = "k" }\ncarries = ["later_than"]\n\n[edge.back]\ncause = "N0"\neffect = "N1"\njoin = { cause = "k", effect = "k" }\ncarries = ["later_than"]\n'
        source = MockDataSource({"t0": [self.ROW], "t1": [self.ROW]})
        result = walk(source, "root_cause", [Start("N0", "1", "k")], self.graph(tmp_path, text))
        for path in result.paths:
            assert len({s.node for s in path}) == len(path)
        assert [len(p) for p in result.paths] == [1] and not result.truncated

    def test_the_same_lookup_is_made_once(self, tmp_path):
        source = MockDataSource({f"t{i}": [self.ROW] for i in range(9)})
        walk(source, "root_cause", [Start("N0", "1", "k"), Start("N0", "1", "k")], self.graph(tmp_path, self.CHAIN))
        lookups = [c[1:5] for c in source.calls if c[0] == "records"]
        assert len(lookups) == len(set(lookups))

    def test_too_many_lookups_stop_the_walk_and_say_so(self, tmp_path):
        rows = [{"k": str(n), "due": "2026-07-01", "done": "2026-07-20"} for n in range(MAX_VISITS + 50)]
        text = self.CHAIN.split("[edge")[0] + '[edge.e0]\ncause = "N1"\neffect = "N0"\njoin = { cause = "k", effect = "k" }\ncarries = ["later_than"]\n'
        source = MockDataSource({"t0": rows, "t1": rows})
        result = walk(source, "root_cause", [Start("N0", "x", "k")], self.graph(tmp_path, text))
        assert not result.truncated
        source.stored["t0"] = rows
        source.records = lambda token, *a, **k: rows if a[0] == "t0" else MockDataSource.records(source, token, *a, **k)
        result = walk(source, "root_cause", [Start("N0", "x", "k")], self.graph(tmp_path, text))
        assert result.truncated and len([c for c in source.calls if c[0] == "records"]) <= MAX_VISITS + 1

    def test_too_many_calls_stop_the_walk_and_say_so(self, tmp_path, monkeypatch):
        monkeypatch.setattr(walk_graph, "MAX_CALLS", 2)
        source = MockDataSource({f"t{i}": [self.ROW] for i in range(9)})
        result = walk(source, "root_cause", [Start("N0", "1", "k")], self.graph(tmp_path, self.CHAIN))
        assert result.truncated and len(source.calls) <= 2


class TestFailuresAndBadInput:
    def test_a_failing_source_fails_the_whole_walk(self):
        source = MockDataSource(SUPPLY)
        source.fail()
        with pytest.raises(DataUnavailable):
            walk(source, "root_cause", [Start("Product", "RM-1002")])

    def test_an_unknown_mode_node_or_missing_key_field_is_refused(self):
        with pytest.raises(ValueError):
            walk(MockDataSource(), "sideways", [Start("Product", "X")])
        with pytest.raises(ValueError):
            walk(MockDataSource(), "root_cause", [Start("Nope", "X")])
        with pytest.raises(ValueError):
            walk(MockDataSource(), "root_cause", [Start("PurchaseDelivery", "X")])
