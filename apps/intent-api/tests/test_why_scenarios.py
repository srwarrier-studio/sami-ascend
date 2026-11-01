import json
from decimal import Decimal

import pytest

pytest.importorskip("butterfly")
pytest.importorskip("synapse_api")
from intent_api.entrypoint.why_eval import EVALS, SCENARIOS, main, run_case

CASES = {case["scenario"]: case for case in json.loads((EVALS / "why.json").read_text())}
FINAL = json.loads((EVALS / "why_final.json").read_text())


def answer(name):
    score, result = run_case(CASES[name])
    return score, result, result["analysis"]


class TestEveryDevelopmentScenarioPasses:
    @pytest.mark.parametrize("name", sorted(CASES))
    def test_the_answer_matches_the_ground_truth(self, name):
        score, _, _ = answer(name)
        assert score.passed, vars(score)


class TestTheSalesStories:
    def test_august_contract_finds_harborline_and_the_piperine_chain_and_explains_most(self):
        _, _, analysis = answer("august-contract")
        assert analysis["significant"] and -16 <= float(analysis["change_percent"]) <= -13
        by_key = {f["key"]: f for f in analysis["findings"]}
        assert 70 <= float(by_key["0000100001"]["share_percent"]) <= 90
        assert [c["key"] for c in by_key["0000100001"]["causes"]] == ["0040000127"]
        assert [c["key"] for c in by_key["RM-1002"]["causes"]] == ["0001000417", "4500001207"]
        assert float(analysis["explained_percent"]) >= 70

    def test_the_may_decoys_are_not_reported(self):
        _, result, _ = answer("august-contract")
        text = json.dumps(result["analysis"])
        assert "MACHINE_BREAKDOWN" not in text and "RAW-2003" not in text

    def test_price_cut_is_a_price_finding_with_no_cause_path(self):
        _, _, analysis = answer("price-cut")
        [finding] = analysis["findings"]
        assert (finding["key"], finding["kind"], finding["paths"]) == ("RM-1001", "price", [])

    def test_a_late_delivery_that_did_not_hurt_sales_is_not_reported(self):
        _, result, analysis = answer("supplier-no-effect")
        assert (analysis["significant"], analysis["findings"]) == (False, [])
        assert "late" not in " ".join(result["lines"])

    def test_a_lost_customer_is_the_largest_finding_and_nothing_explains_it(self):
        _, _, analysis = answer("customer-lost")
        assert analysis["findings"][0]["key"] == "0000100005"
        assert float(analysis["unexplained_percent"]) == 100 and all(not f["explained"] for f in analysis["findings"])

    def test_the_breakdown_is_found_through_the_production_order_and_no_delivery(self):
        _, _, analysis = answer("breakdown-shortfall")
        [finding] = analysis["findings"]
        assert finding["key"] == "RM-1005" and [c["key"] for c in finding["causes"]] == ["0001000420"]
        assert finding["paths"][0][0]["numbers"]["reason"] == "MACHINE_BREAKDOWN"

    def test_a_quiet_month_has_no_findings(self):
        _, result, analysis = answer("quiet-month")
        assert (analysis["significant"], analysis["findings"]) == (False, [])
        assert result["lines"][-1] == "Nothing unusual was found behind this month."


class TestThePurchaseStories:
    def test_a_price_rise_is_a_price_finding_on_black_pepper(self):
        _, _, analysis = answer("purchase-price-rise")
        [finding] = analysis["findings"]
        assert (finding["key"], finding["kind"]) == ("RAW-2002", "price")

    def test_a_bigger_order_is_found_and_left_unexplained(self):
        _, _, analysis = answer("stock-up")
        copper = next(f for f in analysis["findings"] if f["key"] == "RAW-2003")
        assert [c["kind"] for c in copper["causes"]] == ["sum_changed"] and copper["explained"] is False
        assert float(analysis["unexplained_percent"]) == 100

    def test_demand_growth_is_followed_from_purchases_through_production_to_sales(self):
        _, _, analysis = answer("demand-surge")
        steel_coil = analysis["findings"][0]
        assert [(c["source"], c["kind"], c["key"]) for c in steel_coil["causes"]][-1] == ("metric:sales.material", "value_changed", "RM-1002")
        assert steel_coil["explained"] is True

    def test_a_quiet_purchase_month_has_no_findings(self):
        assert answer("quiet-purchases")[2]["findings"] == []


class TestTheEvaluationTool:
    def test_the_development_run_prints_a_summary_and_never_reads_a_held_back_truth(self, capsys, monkeypatch):
        opened = []
        real = type(SCENARIOS).read_text

        def spy(self, *args, **kwargs):
            opened.append(self.name)
            return real(self, *args, **kwargs)

        monkeypatch.setattr(type(SCENARIOS), "read_text", spy)
        main([])
        out = capsys.readouterr().out
        assert "10/10 scenarios passed" in out and "invented 0" in out
        held_back = {p.name for p in SCENARIOS.glob("*.json") if json.loads(real(p))["holdout"]}
        assert held_back and not held_back & set(opened)

    def test_no_development_case_is_a_held_back_scenario(self):
        held_back = {p.stem for p in SCENARIOS.glob("*.json") if json.loads(p.read_text())["holdout"]}
        assert not set(CASES) & held_back
        assert {c["scenario"] for c in FINAL} == held_back


class TestHeldBackScenarios:
    def test_the_final_run_matches_what_the_analyst_did_before_the_move(self, capsys):
        main(["--final"])
        out = capsys.readouterr().out
        assert "11/14 scenarios passed" in out and "invented 0" in out and "blamed wrongly 0" in out
        passing = {line.split()[1][:-1] for line in out.splitlines() if line.startswith("[PASS]")}
        assert {"double-cause"} <= passing


class TestScopeAndCurrency:
    def run(self, name, **kwargs):
        from intent_api.entrypoint.why_eval import run_case as run

        return run(CASES[name], **kwargs)

    def test_the_sentence_names_the_company_and_the_currency(self):
        _, result = self.run("august-contract")
        assert result["lines"][0].startswith("Sales of Sami-Sabinsa fell 14.5% in USD from July 2026 to August 2026")

    def test_the_group_dilutes_the_fall_and_says_so(self):
        _, result = self.run("august-contract", company="all")
        analysis = result["analysis"]
        assert -10 <= float(analysis["change_percent"]) <= -6
        assert result["lines"][0].startswith("Sales of all your companies fell") and result["lines"][-1].startswith("These are the figures of all your companies")

    def test_the_group_still_finds_the_story_customer_first(self):
        _, result = self.run("august-contract", company="all")
        assert result["analysis"]["findings"][0]["key"] == "0000100001"

    def test_rupees_have_no_story_for_the_story_company(self):
        _, result = self.run("august-contract", currency="INR")
        assert result["lines"][0].startswith("There is no data in INR")

    def test_a_company_without_the_story_finds_nothing_in_it(self):
        _, result = self.run("august-contract", company="organica")
        assert result["analysis"]["findings"] == [] or all(not f["explained"] for f in result["analysis"]["findings"])

    def test_a_company_the_user_does_not_have_is_refused_by_synapse_api(self):
        import json

        from intent_api.application.analysis.analyse_question import AnalyseQuestion
        from intent_api.domain.analysis.question import Question
        from intent_api.domain.errors import CompanyNotAllowed
        from intent_api.entrypoint.why_eval import EVAL_TODAY, GRAPH_FILE
        from intent_api.infrastructure.graph_loader import load_graph
        from intent_api.infrastructure.in_process_stack import stack_for

        source, token = stack_for("august-contract", EVAL_TODAY, ("sabinsa",))
        with pytest.raises(CompanyNotAllowed):
            AnalyseQuestion(source.for_company("organica"), load_graph(GRAPH_FILE)).execute(Question("sales", "fall", EVAL_TODAY.replace(month=8, day=1), currency="USD"), token, EVAL_TODAY)
