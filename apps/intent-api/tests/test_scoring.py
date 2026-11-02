from intent_api.application.analysis.score_answer import score

TRUTH = {"causes": [{"type": "contract", "key": "C1"}, {"type": "production_order", "key": "O1"}], "not_blame": [{"type": "purchase_delivery", "key": "P9"}],
         "total_change_percent": [-16, -13], "unexplained": False}


def tag(source, kind, key):
    return {"source": source, "kind": kind, "key": key}


def answer(*groups, change="-14.5", unexplained="20", findings_keys=None):
    findings = []
    for i, group in enumerate(groups):
        steps = [{} for _ in group]
        findings.append({"key": (findings_keys or ["F"] * len(groups))[i], "paths": [steps], "causes": list(group)})
    return {"analysis": {"change_percent": change, "unexplained_percent": unexplained, "findings": findings}}


CONTRACT = tag("record:contract", "coverage_gap", "C1")
ORDER = tag("record:production_order", "later_than", "O1")


class TestScoring:
    def test_every_truth_cause_found_and_nothing_else_is_a_pass(self):
        result = score("s", TRUTH, answer([CONTRACT], [ORDER]))
        assert (result.found, result.missed, result.invented, result.blamed, result.passed) == (["contract C1", "production_order O1"], [], [], [], True)

    def test_a_missed_cause_fails(self):
        result = score("s", TRUTH, answer([CONTRACT]))
        assert result.missed == ["production_order O1"] and not result.passed

    def test_a_confident_wrong_cause_fails_even_when_the_true_ones_are_found(self):
        wrong = tag("record:purchase_delivery", "later_than", "P1")
        result = score("s", TRUTH, answer([CONTRACT], [ORDER], [wrong]))
        assert result.invented == ["later_than P1 (record:purchase_delivery)"] and not result.passed

    def test_a_chain_that_ends_in_a_true_cause_excuses_its_intermediate_steps(self):
        middle = tag("record:production_order", "sum_changed", "OX")
        result = score("s", TRUTH, answer([middle, ORDER], [CONTRACT]))
        assert result.invented == [] and result.passed

    def test_a_not_to_blame_item_that_appears_fails(self):
        result = score("s", TRUTH, answer([CONTRACT, tag("record:purchase_delivery", "later_than", "P9")], [ORDER]))
        assert result.blamed == ["purchase_delivery P9"] and not result.passed

    def test_the_change_must_be_in_the_truth_range(self):
        assert not score("s", TRUTH, answer([CONTRACT], [ORDER], change="-3.0")).passed

    def test_unexplained_is_honoured_when_the_truth_says_so(self):
        truth = {**TRUTH, "causes": [], "unexplained": True, "biggest_mover": "EAST", "total_change_percent": [-20, -12]}
        big = score("s", truth, answer(findings_keys=["EAST"], change="-16.0", unexplained="100"))
        assert big.unexplained_ok
        low = score("s", truth, answer([tag("x", "later_than", "k")], findings_keys=["OTHER"], change="-16.0", unexplained="10"))
        assert not low.unexplained_ok

    def test_a_quiet_truth_wants_no_findings(self):
        truth = {**TRUTH, "causes": [], "not_blame": [], "total_change_percent": [-5, 5]}
        assert score("s", truth, answer(change="-1.0")).passed
        assert not score("s", truth, answer([tag("x", "price_effect", "k")], change="-1.0")).passed

    def test_an_expected_miss_is_reported_as_a_miss(self):
        truth = {**TRUTH, "causes": [{"type": "cancelled_orders", "key": "C"}], "not_blame": []}
        assert score("s", truth, answer([CONTRACT])).missed == ["cancelled_orders C"]

    def test_the_price_supplier_quantity_and_demand_causes_map_onto_the_generic_tags(self):
        truth = {**TRUTH, "not_blame": [], "total_change_percent": [-100, 100], "causes": [
            {"type": "price_change", "key": "M1"}, {"type": "purchase_price_change", "key": "M2"},
            {"type": "purchase_quantity_change", "key": "M3"}, {"type": "supplier_switch", "key": "M4"}, {"type": "demand_growth", "key": "P1"}]}
        tags = [tag("metric:sales.material", "price_effect", "M1"), tag("metric:purchases.material", "price_effect", "M2"),
                tag("record:purchase_delivery", "sum_changed", "M3"), tag("record:purchase_delivery", "set_changed", "M4"), tag("metric:sales.material", "value_changed", "P1")]
        result = score("s", truth, answer(*[[t] for t in tags]))
        assert result.missed == [] and result.invented == [] and result.passed
