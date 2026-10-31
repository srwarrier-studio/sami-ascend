from datetime import date
from decimal import Decimal

from sami_agents.application import anomaly_kinds
from sami_agents.application.anomaly_kinds import coverage_gap, later_than, sum_changed, value_changed
from sami_agents.domain.entities.finding import MemberChange, Window

TODAY = date(2026, 10, 31)
LATE = {"due": "PromisedDeliveryDate", "done": "ActualDeliveryDate", "min_days": 3}
AUGUST = Window.before(date(2026, 8, 1), date(2026, 8, 31))


def delivery(promised, actual):
    return {"PromisedDeliveryDate": promised, "ActualDeliveryDate": actual}


class TestLaterThan:
    def test_twelve_days_late_is_unusual_and_dated_by_its_due_date(self):
        [hit] = later_than([delivery("2026-07-14", "2026-07-26")], LATE, TODAY)
        assert (hit.kind, hit.at) == ("later_than", date(2026, 7, 14))
        assert hit.numbers == {"days_late": 12, "open": False, "due": date(2026, 7, 14), "done": date(2026, 7, 26), "reason": None}

    def test_two_days_late_and_early_are_not(self):
        assert later_than([delivery("2026-07-14", "2026-07-16"), delivery("2026-07-14", "2026-07-10")], LATE, TODAY) == []

    def test_exactly_the_minimum_counts(self):
        assert len(later_than([delivery("2026-07-14", "2026-07-17")], LATE, TODAY)) == 1

    def test_an_open_item_overdue_counts_to_today(self):
        [hit] = later_than([delivery("2026-10-20", None)], LATE, TODAY)
        assert (hit.numbers["days_late"], hit.numbers["open"], hit.numbers["done"]) == (11, True, None)

    def test_an_open_item_not_yet_due_is_not_late(self):
        assert later_than([delivery("2026-11-20", None)], LATE, TODAY) == []

    def test_each_late_row_is_its_own_hit_with_its_row_as_evidence(self):
        rows = [delivery("2026-07-14", "2026-07-26"), delivery("2026-06-01", "2026-06-02"), delivery("2026-05-01", "2026-05-10")]
        hits = later_than(rows, LATE, TODAY)
        assert [h.rows for h in hits] == [[rows[0]], [rows[2]]]


class TestCoverageGap:
    PARAMS = {"from": "ValidFrom", "to": "ValidTo"}

    def contract(self, first, last):
        return {"ValidFrom": first, "ValidTo": last}

    def test_a_contract_that_ended_in_july_leaves_all_of_august_uncovered(self):
        [hit] = coverage_gap([self.contract("2025-07-13", "2026-07-12")], self.PARAMS, AUGUST)
        assert hit.numbers == {"days_uncovered": 31, "first_uncovered": date(2026, 8, 1), "last_uncovered": date(2026, 8, 31)}
        assert hit.at == date(2026, 8, 1)

    def test_a_renewal_that_starts_in_september_leaves_the_same_gap(self):
        rows = [self.contract("2025-07-13", "2026-07-12"), self.contract("2026-09-14", "2027-09-13")]
        assert coverage_gap(rows, self.PARAMS, AUGUST)[0].numbers["days_uncovered"] == 31

    def test_two_contracts_back_to_back_leave_none(self):
        rows = [self.contract("2025-07-13", "2026-08-15"), self.contract("2026-08-16", "2027-08-15")]
        assert coverage_gap(rows, self.PARAMS, AUGUST) == []

    def test_a_contract_covering_the_window_leaves_none(self):
        assert coverage_gap([self.contract("2026-01-01", "2026-12-31")], self.PARAMS, AUGUST) == []

    def test_a_gap_in_the_middle_is_counted_and_dated_by_its_first_day(self):
        rows = [self.contract("2026-01-01", "2026-08-10"), self.contract("2026-08-20", "2026-12-31")]
        [hit] = coverage_gap(rows, self.PARAMS, AUGUST)
        assert (hit.numbers["days_uncovered"], hit.at, hit.numbers["last_uncovered"]) == (9, date(2026, 8, 11), date(2026, 8, 19))

    def test_no_rows_at_all_is_a_gap_over_the_whole_window(self):
        assert coverage_gap([], self.PARAMS, AUGUST)[0].numbers["days_uncovered"] == 31

    def test_an_open_ended_row_covers_to_the_end_of_the_window(self):
        assert coverage_gap([self.contract("2026-01-01", None)], self.PARAMS, AUGUST) == []


class TestSumChanged:
    PARAMS = {"field": "Qty", "date": "Ordered", "min_percent": 10, "pad_days": 30}
    WINDOW = Window.before(date(2026, 7, 1), date(2026, 9, 30))

    def rows(self, previous, current):
        return [{"Qty": str(previous), "Ordered": "2026-05-10"}, {"Qty": str(current), "Ordered": "2026-08-10"}]

    def test_a_rise_of_23_percent_is_unusual(self):
        [hit] = sum_changed(self.rows(100, 123), self.PARAMS, self.WINDOW)
        assert (hit.numbers["current"], hit.numbers["previous"], hit.numbers["change_percent"], hit.at) == (Decimal(123), Decimal(100), Decimal("23.00"), None)

    def test_five_percent_is_not(self):
        assert sum_changed(self.rows(100, 105), self.PARAMS, self.WINDOW) == []

    def test_a_fall_counts_too(self):
        assert sum_changed(self.rows(100, 80), self.PARAMS, self.WINDOW)[0].numbers["change_percent"] == Decimal("-20.00")

    def test_rows_are_placed_by_their_own_date_and_others_are_ignored(self):
        rows = self.rows(100, 100) + [{"Qty": "999", "Ordered": "2025-01-01"}, {"Qty": "999", "Ordered": "2026-12-01"}]
        assert sum_changed(rows, self.PARAMS, self.WINDOW) == []

    def test_the_evidence_is_the_rows_in_the_window(self):
        [hit] = sum_changed(self.rows(100, 150), self.PARAMS, self.WINDOW)
        assert [r["Ordered"] for r in hit.rows] == ["2026-08-10"]

    def test_something_from_nothing_is_unusual_and_nothing_from_nothing_is_not(self):
        assert sum_changed([{"Qty": "5", "Ordered": "2026-08-10"}], self.PARAMS, self.WINDOW)[0].numbers["change_percent"] is None
        assert sum_changed([], self.PARAMS, self.WINDOW) == []


class TestValueChanged:
    PARAMS = {"min_percent": 10}

    def test_a_fall_of_15_percent_is_unusual_and_carries_its_effects(self):
        change = MemberChange(Decimal("85.00"), Decimal("100.00"), Decimal("-15.00"), Decimal("0.00"), Decimal("-15.00"))
        [hit] = value_changed(change, self.PARAMS)
        assert hit.numbers["change_percent"] == Decimal("-15.00") and hit.numbers["price_effect"] == Decimal("-15.00")

    def test_a_small_change_is_not(self):
        assert value_changed(MemberChange(Decimal("104"), Decimal("100"), Decimal("4.00")), self.PARAMS) == []

    def test_a_member_that_was_not_found_is_not(self):
        assert value_changed(None, self.PARAMS) == []

    def test_a_new_member_is_unusual(self):
        assert len(value_changed(MemberChange(Decimal("5"), Decimal("0"), None), self.PARAMS)) == 1


class TestWindow:
    def test_the_previous_period_is_the_same_length_directly_before(self):
        w = Window.before(date(2026, 8, 1), date(2026, 8, 31))
        assert (w.compare_start, w.compare_end, w.days) == (date(2026, 7, 1), date(2026, 7, 31), 31)

    def test_widening_back_moves_the_start_and_the_comparison(self):
        w = Window.before(date(2026, 8, 1), date(2026, 8, 31)).widened_back(60)
        assert (w.start, w.end, w.compare_end) == (date(2026, 6, 2), date(2026, 8, 31), date(2026, 6, 1))
        assert (w.compare_end - w.compare_start).days + 1 == w.days

    def test_widening_forward_moves_the_end(self):
        w = Window.before(date(2026, 8, 1), date(2026, 8, 31)).widened_forward(30, TODAY)
        assert (w.start, w.end, w.compare_end) == (date(2026, 8, 1), date(2026, 9, 30), date(2026, 7, 31))

    def test_widening_forward_stops_at_today(self):
        w = Window.before(date(2026, 8, 1), date(2026, 8, 31)).widened_forward(90, date(2026, 9, 10))
        assert w.end == date(2026, 9, 10)

    def test_a_window_never_grows_past_170_days(self):
        back = Window.before(date(2026, 8, 1), date(2026, 8, 31)).widened_back(400)
        assert back.days == 170 and back.end == date(2026, 8, 31)
        forward = Window.before(date(2026, 1, 1), date(2026, 1, 31)).widened_forward(400, TODAY)
        assert forward.days == 170

    def test_the_span_covers_both_periods_with_padding(self):
        assert Window.before(date(2026, 8, 1), date(2026, 8, 31)).span(30) == (date(2026, 6, 1), date(2026, 9, 30))


class TestSetChanged:
    PARAMS = {"field": "Supplier", "date": "OrderDate", "pad_days": 30}
    WINDOW = Window.before(date(2026, 10, 1), date(2026, 10, 31))

    def row(self, supplier, ordered):
        return {"Supplier": supplier, "OrderDate": ordered}

    def test_a_new_supplier_is_reported_with_the_old_one_still_there(self):
        rows = [self.row("S1", "2026-09-10"), self.row("S1", "2026-10-10"), self.row("S2", "2026-10-12")]
        [hit] = anomaly_kinds.set_changed(rows, self.PARAMS, self.WINDOW)
        assert (hit.kind, hit.at, hit.numbers) == ("set_changed", None, {"field": "Supplier", "new": ["S2"], "gone": []})
        assert {r["Supplier"] for r in hit.rows} == {"S1", "S2"}

    def test_a_supplier_that_stopped_is_gone(self):
        rows = [self.row("S1", "2026-09-10"), self.row("S2", "2026-09-12"), self.row("S2", "2026-10-12")]
        [hit] = anomaly_kinds.set_changed(rows, self.PARAMS, self.WINDOW)
        assert hit.numbers == {"field": "Supplier", "new": [], "gone": ["S1"]}

    def test_the_same_suppliers_in_both_periods_is_nothing(self):
        rows = [self.row("S1", "2026-09-10"), self.row("S1", "2026-10-10")]
        assert anomaly_kinds.set_changed(rows, self.PARAMS, self.WINDOW) == []

    def test_rows_outside_both_periods_and_empty_values_are_ignored(self):
        rows = [self.row("S1", "2026-09-10"), self.row("S1", "2026-10-10"), self.row("S9", "2025-01-01"), self.row(None, "2026-10-11"), self.row("", "2026-10-11")]
        assert anomaly_kinds.set_changed(rows, self.PARAMS, self.WINDOW) == []


class TestLaterThanReason:
    def test_the_reason_is_carried_when_the_parameter_names_a_field(self):
        params = {**LATE, "reason": "DelayReason"}
        [hit] = later_than([{**delivery("2026-07-14", "2026-07-26"), "DelayReason": "MATERIAL_SHORTAGE"}], params, TODAY)
        assert hit.numbers["reason"] == "MATERIAL_SHORTAGE"
