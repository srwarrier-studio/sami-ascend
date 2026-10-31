from datetime import date
from decimal import Decimal

import pytest

from sami_agents.application import walk_graph
from sami_agents.application.analyse_question import AnalyseQuestion, Thresholds, percent, window_of
from sami_agents.domain.entities.finding import Window
from sami_agents.domain.entities.measure import Comparison, DimensionInfo, MetricInfo, MoverRow
from sami_agents.domain.entities.question import Question
from sami_agents.domain.errors import DataUnavailable
from sami_agents.infrastructure.graph_loader import load_graph
from sami_agents.infrastructure.mock_data_source import MockDataSource
from sami_agents.infrastructure.settings import GRAPH_FILE

TODAY = date(2026, 10, 31)
GRAPH = load_graph(GRAPH_FILE)
INFOS = [
    MetricInfo("sales", "Sales", (DimensionInfo("customer", False), DimensionInfo("material", True))),
    MetricInfo("purchases", "Purchases", (DimensionInfo("supplier", False), DimensionInfo("material", True))),
]
AUGUST = Question("sales", "fall", date(2026, 8, 1))


def total(current, previous, currency="INR"):
    change = Decimal(current) - Decimal(previous)
    return Comparison(currency, Decimal(current), Decimal(previous), change, percent(change, Decimal(previous)))


def row(key, current, previous, share=None, name=None, volume=None, price=None):
    return MoverRow(key, name or f"Name {key}", Decimal(current), Decimal(previous), Decimal(current) - Decimal(previous), None if share is None else Decimal(share), "KG" if volume is not None else None, None if volume is None else Decimal(volume), None if price is None else Decimal(price))


def with_rows(grand, rows, currency="INR"):
    return Comparison(currency, grand.current, grand.previous, grand.change, grand.change_percent, rows)


def analyse(comparisons, records=None, question=AUGUST, thresholds=Thresholds(), changes=None):
    source = MockDataSource(records or {}, changes, INFOS, comparisons)
    return AnalyseQuestion(source, GRAPH, thresholds).execute(question, "tok", TODAY), source


GRAND = total("900", "1000")


def covering(*keys):
    return [{"SalesContract": f"C-{key}", "SoldToParty": key, "ValidFrom": "2026-01-01", "ValidTo": "2027-01-01"} for key in keys]


def fall_by_customer(rows):
    return {("sales", None): [GRAND], ("sales", "customer"): [with_rows(GRAND, rows)]}


class TestTheWindow:
    def test_the_previous_period_is_the_previous_calendar_month(self):
        w = window_of(date(2026, 9, 1))
        assert (w.start, w.end, w.compare_start, w.compare_end) == (date(2026, 9, 1), date(2026, 9, 30), date(2026, 8, 1), date(2026, 8, 31))

    def test_january_compares_with_december_and_march_with_february(self):
        assert (window_of(date(2026, 1, 1)).compare_start, window_of(date(2026, 1, 1)).compare_end) == (date(2025, 12, 1), date(2025, 12, 31))
        assert window_of(date(2026, 3, 1)).compare_end == date(2026, 2, 28)


class TestHeadline:
    def test_the_totals_and_whether_the_change_is_significant(self):
        analysis, _ = analyse({("sales", None): [GRAND]})
        assert (analysis.currency, analysis.current, analysis.previous, analysis.change, analysis.change_percent, analysis.significant) == ("INR", Decimal(900), Decimal(1000), Decimal(-100), Decimal("-10.00"), True)

    def test_five_percent_is_significant_and_just_under_is_not(self):
        assert analyse({("sales", None): [total("950", "1000")]})[0].significant is True
        assert analyse({("sales", None): [total("951", "1000")]})[0].significant is False

    def test_no_data_says_so(self):
        analysis, _ = analyse({})
        assert analysis.findings == [] and "no data" in analysis.limits[0].lower()

    def test_a_metric_that_is_not_registered_is_unavailable(self):
        with pytest.raises(DataUnavailable):
            AnalyseQuestion(MockDataSource(), GRAPH).execute(AUGUST, "tok", TODAY)

    def test_more_than_one_currency_is_said_in_the_limits(self):
        analysis, _ = analyse({("sales", None): [GRAND, total("5", "6", "USD")]})
        assert any("Only INR" in text for text in analysis.limits)


class TestWhichMoversAreNotable:
    def movers(self, rows, **thresholds):
        analysis, source = analyse(fall_by_customer(rows), {"contract": covering("A", "B")}, thresholds=Thresholds(**thresholds))
        return [f.key for f in analysis.findings], source

    def test_a_member_must_move_ten_percent_itself(self):
        keys, _ = self.movers([row("A", "9100", "10000", "100")])
        assert keys == []
        keys, _ = self.movers([row("A", "8900", "10000", "100")])
        assert keys == ["A"]

    def test_ten_percent_and_enough_of_the_total_is_notable(self):
        grand = total("90000", "100000")
        analysis, _ = analyse({("sales", None): [grand], ("sales", "customer"): [with_rows(grand, [row("A", "8000", "10000", "20"), row("B", "9100", "10000", "9")])]}, {"contract": covering("A", "B")})
        assert [f.key for f in analysis.findings] == ["A"]

    def test_a_big_percent_of_a_tiny_member_is_not_notable(self):
        grand = total("90000", "100000")
        analysis, _ = analyse({("sales", None): [grand], ("sales", "customer"): [with_rows(grand, [row("T", "10", "50", "0.04")])]})
        assert analysis.findings == []

    def test_the_other_row_is_never_a_finding(self):
        analysis, _ = analyse(fall_by_customer([row("other", "10", "500", "50")]))
        assert analysis.findings == []

    def test_a_mover_that_is_not_notable_is_never_walked(self):
        records = {"contract": []}
        _, source = analyse(fall_by_customer([row("A", "99", "100", "1")]), records)
        assert not [c for c in source.calls if c[0] == "records"]


class TestDirections:
    ROWS = [row("DOWN", "700", "1000", "300"), row("UP", "1100", "1000", "-100")]

    def lists(self, direction):
        analysis, _ = analyse(fall_by_customer(self.ROWS), question=Question("sales", direction, date(2026, 8, 1)))
        return [f.key for f in analysis.findings], [f.key for f in analysis.offsets]

    def test_for_a_fall_the_fallers_are_findings_and_the_risers_offsets(self):
        assert self.lists("fall") == (["DOWN"], ["UP"])

    def test_for_a_rise_it_is_the_other_way_round(self):
        assert self.lists("rise") == (["UP"], ["DOWN"])

    def test_for_a_change_both_are_findings(self):
        assert sorted(self.lists("change")[0]) == ["DOWN", "UP"] and self.lists("change")[1] == []


class TestPriceFindings:
    def finding(self, price, volume="0.00"):
        grand = total("1000", "2000")
        comparisons = {("sales", None): [grand], ("sales", "customer"): [with_rows(grand, [])], ("sales", "material"): [with_rows(grand, [row("M", "1000", "2000", "100", volume=volume, price=price)])]}
        return analyse(comparisons)[0].findings[0]

    def test_a_price_effect_of_half_the_change_or_more_is_a_price_finding(self):
        f = self.finding("-500.00", "-500.00")
        assert (f.kind, f.explained) == ("price", True)
        assert f.causes[0].__dict__ == {"source": "metric:sales.material", "kind": "price_effect", "key": "M"}

    def test_just_under_half_is_a_volume_finding(self):
        f = self.finding("-490.00", "-510.00")
        assert (f.kind, f.explained) == ("volume", False)

    def test_a_price_finding_needs_no_walk(self):
        grand = total("1000", "2000")
        source = MockDataSource({}, None, INFOS, {("sales", None): [grand], ("sales", "customer"): [], ("sales", "material"): [with_rows(grand, [row("M", "1000", "2000", "100", volume="0.00", price="-1000.00")])]})
        AnalyseQuestion(source, GRAPH).execute(AUGUST, "tok", TODAY)
        assert not [c for c in source.calls if c[0] == "records"]


class TestWalkingAndTheCauses:
    CONTRACT = {"SalesContract": "0040000127", "SoldToParty": "ACME", "ValidFrom": "2025-07-13", "ValidTo": "2026-07-12"}

    def acme(self, records=None):
        grand = total("900", "1000")
        rows = [row("ACME", "100", "900", "800", name="Acme Industries")]
        return analyse({("sales", None): [grand], ("sales", "customer"): [with_rows(grand, rows)]}, records or {"contract": [self.CONTRACT]})[0]

    def test_a_notable_customer_is_walked_and_its_cause_found_with_the_contract_number(self):
        finding = self.acme().findings[0]
        assert [(c.source, c.kind, c.key) for c in finding.causes] == [("record:contract", "coverage_gap", "0040000127")]
        assert finding.explained is True and len(finding.paths) == 1

    def test_without_a_cause_the_finding_stays_unexplained(self):
        finding = self.acme({"contract": [{**self.CONTRACT, "ValidTo": "2027-01-01"}]}).findings[0]
        assert (finding.paths, finding.causes, finding.explained) == ([], [], False)

    def test_a_dimension_without_a_graph_node_is_measured_but_not_walked(self):
        grand = total("900", "1000")
        analysis, source = analyse({("purchases", None): [grand], ("purchases", "supplier"): [with_rows(grand, [row("S1", "100", "900", "800")])]}, question=Question("purchases", "fall", date(2026, 8, 1)))
        assert analysis.findings[0].paths == [] and not [c for c in source.calls if c[0] == "records"]

    def test_a_search_that_hits_its_limit_is_said_in_the_limits(self, monkeypatch):
        monkeypatch.setattr(walk_graph, "MAX_CALLS", 1)
        records = {"production_order": [{"ProductionOrder": "O1", "Material": "RM-1002", "PlannedStartDate": "2026-07-06", "PlannedEndDate": "2026-07-20", "ActualEndDate": "2026-08-03"}], "production_component": [{"ProductionOrder": "O1", "Material": "RAW-2002"}]}
        grand = total("900", "1000")
        analysis, _ = analyse({("sales", None): [grand], ("sales", "customer"): [], ("sales", "material"): [with_rows(grand, [row("RM-1002", "100", "900", "800", volume="-800.00", price="0.00")])]}, records)
        assert any("limit" in text for text in analysis.limits)

    def test_a_failing_source_fails_the_analysis(self):
        source = MockDataSource({}, None, INFOS, {("sales", None): [GRAND]})
        source.failing = False
        source.compare = lambda *a, **k: (_ for _ in ()).throw(DataUnavailable("down"))
        with pytest.raises(DataUnavailable):
            AnalyseQuestion(source, GRAPH).execute(AUGUST, "tok", TODAY)


class TestWhatCountsAsExplained:
    def explained(self, records, material="RM-1002"):
        grand = total("900", "1000")
        comparisons = {("sales", None): [grand], ("sales", "customer"): [], ("sales", "material"): [with_rows(grand, [row(material, "100", "900", "80", volume="-800.00", price="0.00")])]}
        return analyse(comparisons, records)[0].findings[0]

    LATE_ORDER = {"ProductionOrder": "O1", "Material": "RM-1002", "PlannedStartDate": "2026-07-06", "PlannedEndDate": "2026-07-20", "ActualEndDate": "2026-08-03"}

    def test_a_late_step_explains(self):
        f = self.explained({"production_order": [self.LATE_ORDER], "production_component": [{"ProductionOrder": "O1", "Material": "RAW-2002"}]})
        assert f.explained and [c.kind for c in f.causes] == ["later_than"] and f.causes[0].key == "O1"

    def test_a_chain_of_two_steps_explains_even_when_both_only_restate(self):
        f = self.explained({"production_order": [self.LATE_ORDER], "production_component": [{"ProductionOrder": "O1", "Material": "RAW-2002"}],
                            "purchase_delivery": [{"PurchaseOrder": "P1", "Material": "RAW-2002", "PromisedDeliveryDate": "2026-07-14", "ActualDeliveryDate": "2026-07-26"}]})
        assert f.explained and [c.key for c in f.causes] == ["O1", "P1"]


class TestRankingAndTheUnexplainedRest:
    def two_dimensions(self, customer_rows, material_rows, others=()):
        grand = total("900", "1000")
        return analyse({("sales", None): [grand], ("sales", "customer"): [with_rows(grand, customer_rows)], ("sales", "material"): [with_rows(grand, material_rows)]},
                       {"contract": [TestWalkingAndTheCauses.CONTRACT, *others]})[0]

    def price_row(self, key, share):
        return row(key, "500", "1000", share, volume="-100.00", price="-400.00")

    def test_findings_are_ordered_by_share_largest_first(self):
        analysis = self.two_dimensions([row("A", "700", "1000", "30"), row("B", "500", "1000", "50"), row("C", "800", "1000", "20")], [], covering("A", "B", "C"))
        assert [f.key for f in analysis.findings] == ["B", "A", "C"]

    def test_explained_is_the_larger_dimension_not_the_two_added(self):
        analysis = self.two_dimensions([row("ACME", "100", "900", "70", name="Acme")], [self.price_row("M1", "60")])
        assert (analysis.explained_percent, analysis.unexplained_percent) == (Decimal(70), Decimal(30))

    def test_a_dimension_over_one_hundred_is_capped(self):
        analysis = self.two_dimensions([], [self.price_row("M1", "130")])
        assert (analysis.explained_percent, analysis.unexplained_percent) == (Decimal(100), Decimal(0))

    def test_findings_with_no_cause_leave_everything_unexplained(self):
        analysis = self.two_dimensions([row("A", "700", "1000", "100")], [], covering("A"))
        assert (analysis.explained_percent, analysis.unexplained_percent) == (Decimal(0), Decimal(100))

    def test_only_explained_findings_count_towards_the_share(self):
        analysis = self.two_dimensions([row("ACME", "100", "900", "40", name="Acme"), row("B", "500", "1000", "35")], [], covering("B"))
        assert analysis.explained_percent == Decimal(40)

    def test_a_wrong_premise_leaves_nothing_explained(self):
        rows = [row("UP", "1500", "1000", "-50")]
        analysis, _ = analyse({("sales", None): [GRAND], ("sales", "customer"): [with_rows(GRAND, [row("DOWN", "700", "1000", "-30")])]})
        assert analysis.explained_percent == Decimal(0)

    def test_the_tables_keep_every_row_of_every_dimension(self):
        analysis = self.two_dimensions([row("A", "700", "1000", "30"), row("other", "1", "2", "1")], [row("M", "5", "5", "0")], covering("A"))
        assert [r.key for r in analysis.tables["customer"]] == ["A", "other"] and [r.key for r in analysis.tables["material"]] == ["M"]


class TestWhenTheTotalHardlyMoves:
    STEADY = total("990", "1000")

    def analyse(self, rows, records=None):
        return analyse({("sales", None): [self.STEADY], ("sales", "customer"): [with_rows(self.STEADY, rows)]}, records)[0]

    def test_movers_without_a_cause_are_left_out_and_so_are_offsets(self):
        analysis = self.analyse([row("A", "700", "1000", "3000"), row("B", "1300", "1000", "-3000")], {"contract": covering("A", "B")})
        assert (analysis.significant, analysis.findings, analysis.offsets) == (False, [], [])

    def test_a_mover_with_a_cause_is_still_reported(self):
        analysis = self.analyse([row("ACME", "100", "900", "8000")], {"contract": [TestWalkingAndTheCauses.CONTRACT]})
        assert [f.key for f in analysis.findings] == ["ACME"]
