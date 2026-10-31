from datetime import date

import pytest

from synapse_api.application.read_records import ReadRecords
from synapse_api.domain.errors import InvalidQuery, RecordTypeNotFound, SapUnavailable
from synapse_api.infrastructure.mock_record_source import MockRecordSource
from synapse_api.infrastructure.registry_loader import load_registry
from synapse_api.infrastructure.settings import REGISTRY_PATH

REGISTRY = load_registry(REGISTRY_PATH)
TODAY = date(2026, 10, 31)
JULY = (date(2026, 7, 1), date(2026, 7, 31))


def contract(number, customer, valid_from, valid_to):
    return {"SalesContract": number, "SoldToParty": customer, "ValidFrom": valid_from, "ValidTo": valid_to}


def delivery(order, material, promised, actual, supplier="S1"):
    return {"PurchaseOrder": order, "Material": material, "Supplier": supplier, "PromisedDeliveryDate": promised, "ActualDeliveryDate": actual}


def production(order, material, start, end, actual):
    return {"ProductionOrder": order, "Material": material, "PlannedStartDate": start, "PlannedEndDate": end, "ActualEndDate": actual}


def read(rows, type_name, key, key_field=None, window=JULY, today=TODAY):
    source = MockRecordSource(rows)
    start, end = window if window else (None, None)
    return ReadRecords(source, REGISTRY).execute(type_name, key, key_field, start, end, today)


class TestContracts:
    ROWS = {"contract": [
        contract("C1", "ACME", "2025-07-13", "2026-07-12"),
        contract("C2", "ACME", "2026-09-14", "2027-09-13"),
        contract("C3", "OTHER", "2025-01-01", "2026-12-31"),
    ]}

    def test_the_contract_valid_in_the_window_for_the_customer(self):
        field, rows = read(self.ROWS, "contract", "ACME", window=(date(2026, 7, 1), date(2026, 8, 31)))
        assert (field, [r["SalesContract"] for r in rows]) == ("SoldToParty", ["C1"])

    def test_a_later_window_finds_the_renewal(self):
        _, rows = read(self.ROWS, "contract", "ACME", window=(date(2026, 9, 1), date(2026, 9, 30)))
        assert [r["SalesContract"] for r in rows] == ["C2"]

    def test_a_contract_can_be_found_by_its_number(self):
        field, rows = read(self.ROWS, "contract", "C3", "SalesContract")
        assert (field, len(rows)) == ("SalesContract", 1)

    def test_contracts_have_no_delay_days(self):
        _, rows = read(self.ROWS, "contract", "ACME")
        assert "delay_days" not in rows[0]

    def test_rows_are_ordered_by_the_types_order(self):
        _, rows = read(self.ROWS, "contract", "ACME", window=(date(2026, 1, 1), date(2026, 12, 31)))
        assert [r["SalesContract"] for r in rows] == ["C1", "C2"]

    def test_nothing_found_is_an_empty_list(self):
        assert read(self.ROWS, "contract", "NOBODY")[1] == []


class TestDeliveries:
    def test_promised_before_the_window_and_delivered_inside_is_returned(self):
        rows = {"purchase_delivery": [delivery("P1", "RAW", "2026-06-25", "2026-07-05")]}
        assert len(read(rows, "purchase_delivery", "RAW")[1]) == 1

    def test_delivered_before_the_window_is_not(self):
        rows = {"purchase_delivery": [delivery("P1", "RAW", "2026-06-20", "2026-06-28")]}
        assert read(rows, "purchase_delivery", "RAW")[1] == []

    def test_delivered_early_is_found_by_either_date(self):
        rows = {"purchase_delivery": [delivery("P1", "RAW", "2026-07-10", "2026-06-30")]}
        assert len(read(rows, "purchase_delivery", "RAW")[1]) == 1

    def test_an_open_overdue_item_is_returned_for_a_window_with_today(self):
        rows = {"purchase_delivery": [delivery("P1", "RAW", "2026-09-20", None)]}
        assert len(read(rows, "purchase_delivery", "RAW", window=(date(2026, 10, 25), date(2026, 10, 31)))[1]) == 1
        assert read(rows, "purchase_delivery", "RAW", window=(date(2026, 8, 1), date(2026, 8, 31)))[1] == []

    def test_an_open_item_not_yet_due_is_returned_for_its_promised_window_only(self):
        rows = {"purchase_delivery": [delivery("P1", "RAW", "2026-11-20", None)]}
        assert len(read(rows, "purchase_delivery", "RAW", window=(date(2026, 11, 15), date(2026, 11, 30)))[1]) == 1
        assert read(rows, "purchase_delivery", "RAW", window=(date(2026, 10, 1), date(2026, 10, 31)))[1] == []

    def test_delay_days_late_on_time_and_open(self):
        rows = {"purchase_delivery": [
            delivery("LATE", "RAW", "2026-07-14", "2026-07-26"),
            delivery("EARLY", "RAW", "2026-07-14", "2026-07-10"),
            delivery("OPEN-LATE", "RAW", "2026-10-20", None),
            delivery("OPEN-FUTURE", "RAW", "2026-11-20", None),
        ]}
        _, found = read(rows, "purchase_delivery", "RAW", window=(date(2026, 7, 1), date(2026, 11, 30)))
        assert {r["PurchaseOrder"]: r["delay_days"] for r in found} == {"LATE": 12, "EARLY": 0, "OPEN-LATE": 11, "OPEN-FUTURE": 0}

    def test_lookup_by_supplier(self):
        rows = {"purchase_delivery": [delivery("P1", "RAW", "2026-07-14", "2026-07-15", "S9"), delivery("P2", "RAW", "2026-07-14", "2026-07-15", "S1")]}
        _, found = read(rows, "purchase_delivery", "S9", "Supplier")
        assert [r["PurchaseOrder"] for r in found] == ["P1"]


class TestProduction:
    def test_a_late_order_has_its_delay_and_its_reason_passes_through(self):
        order = {**production("O1", "RM-1002", "2026-07-06", "2026-07-20", "2026-08-03"), "DelayReason": "MATERIAL_SHORTAGE"}
        _, [found] = read({"production_order": [order]}, "production_order", "RM-1002", window=(date(2026, 7, 1), date(2026, 8, 31)))
        assert (found["delay_days"], found["DelayReason"]) == (14, "MATERIAL_SHORTAGE")

    def test_a_running_order_is_active_until_its_planned_end_or_today(self):
        rows = {"production_order": [production("O1", "RM-1002", "2026-10-01", "2026-10-15", None)]}
        assert len(read(rows, "production_order", "RM-1002", window=(date(2026, 10, 25), date(2026, 10, 31)))[1]) == 1


class TestComponents:
    ROWS = {"production_component": [
        {"ProductionOrder": "O1", "Material": "RAW-2002", "RequiredQuantity": "4400.000"},
        {"ProductionOrder": "O2", "Material": "RAW-2002", "RequiredQuantity": "1.000"},
    ]}

    def test_components_of_an_order_need_no_window(self):
        field, rows = read(self.ROWS, "production_component", "O1", window=None)
        assert (field, len(rows)) == ("ProductionOrder", 1)

    def test_a_window_is_ignored(self):
        assert len(read(self.ROWS, "production_component", "O1")[1]) == 1

    def test_orders_that_use_a_material(self):
        _, rows = read(self.ROWS, "production_component", "RAW-2002", "Material", window=None)
        assert [r["ProductionOrder"] for r in rows] == ["O1", "O2"]


class TestInvalid:
    @pytest.mark.parametrize(
        "type_name,key,key_field,window",
        [
            ("contract", "ACME", "Nope", JULY),
            ("contract", "AC'ME", None, JULY),
            ("contract", "AC ME", None, JULY),
            ("contract", "A" * 41, None, JULY),
            ("contract", "", None, JULY),
            ("contract", "ACME", None, (date(2026, 7, 31), date(2026, 7, 1))),
            ("contract", "ACME", None, (date(2025, 1, 1), date(2026, 7, 31))),
            ("contract", "ACME", None, None),
        ],
    )
    def test_each_rule(self, type_name, key, key_field, window):
        with pytest.raises(InvalidQuery):
            read({}, type_name, key, key_field, window)

    def test_an_unknown_type(self):
        with pytest.raises(RecordTypeNotFound):
            read({}, "invoice", "X")

    def test_a_key_of_exactly_40_characters_is_allowed(self):
        read({}, "contract", "A" * 40)

    def test_a_failing_source_returns_nothing(self):
        source = MockRecordSource()
        source.fail()
        with pytest.raises(SapUnavailable):
            ReadRecords(source, REGISTRY).execute("contract", "ACME", None, *JULY, TODAY)
