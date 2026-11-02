import pytest

from intent_api.entrypoint.graph import main

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


def run(args, capsys):
    with pytest.raises(SystemExit) as stop:
        main(args)
    return stop.value.code, capsys.readouterr().out


class TestCheck:
    def test_the_shipped_graph_prints_ok_and_exits_zero(self, capsys):
        code, out = run(["check"], capsys)
        assert code == 0 and out.rstrip().endswith("ok")

    def test_problems_are_printed_one_per_line_and_exit_one(self, tmp_path, capsys):
        path = tmp_path / "g.toml"
        path.write_text(GOOD.replace("record:contract", "record:deal") + '\n[node.Lonely]\nsource = "record:contract"\n')
        code, out = run(["check", "--graph", str(path)], capsys)
        assert code == 1
        assert "record type 'deal' is not in the registry" in out and "node 'Lonely': no edge touches it" in out
        assert "ok" not in out.splitlines()

    def test_a_file_that_does_not_load_exits_one_with_its_problems(self, tmp_path, capsys):
        path = tmp_path / "g.toml"
        path.write_text(GOOD.replace("metric:sales.customer", "nonsense"))
        code, out = run(["check", "--graph", str(path)], capsys)
        assert code == 1 and "node 'Customer': 'source' must look like" in out


class TestShow:
    def test_text_lists_nodes_and_edges(self, capsys):
        code, out = run(["show"], capsys)
        assert code == 0 and out.startswith("Nodes") and "Edges (cause -> effect)" in out

    def test_mermaid_prints_a_diagram(self, capsys):
        code, out = run(["show", "--mermaid"], capsys)
        assert code == 0 and out.startswith("graph LR")

    def test_a_bad_file_exits_one(self, tmp_path, capsys):
        path = tmp_path / "g.toml"
        path.write_text("not = [valid")
        assert run(["show", "--graph", str(path)], capsys)[0] == 1
