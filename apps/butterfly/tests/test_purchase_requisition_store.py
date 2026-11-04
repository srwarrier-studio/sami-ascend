from dataclasses import replace
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from butterfly.domain.entities.purchase_requisition import PurchaseRequisition, PurchaseRequisitionItem
from butterfly.domain.entities.release_rule import RELEASE_RULES, ReleaseRule, rule_for
from butterfly.infrastructure.memory.in_memory_purchase_requisition_repo import InMemoryPurchaseRequisitionRepo
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.purchase_requisition_repo import SqlitePurchaseRequisitionRepo

NOW = datetime(2026, 11, 4, 10, 0, tzinfo=timezone.utc)


def item(number: str, line: str = "10", **changes) -> PurchaseRequisitionItem:
    base = PurchaseRequisitionItem(
        number, line, "MZ-TG-A11", "Lithium Ion Battery", "L001", Decimal("10.000"), "PC", Decimal("20.00"), "INR", "1010", "INA1", "1010", "002", date(2026, 12, 1)
    )
    return replace(base, **changes)


def requisition(number: str, *items: PurchaseRequisitionItem) -> PurchaseRequisition:
    return PurchaseRequisition(number, "NB", "", "purchase1", NOW, NOW, list(items))


@pytest.fixture(params=["memory", "sqlite"])
def repo(request):
    return InMemoryPurchaseRequisitionRepo() if request.param == "memory" else SqlitePurchaseRequisitionRepo(Database())


class TestNumberRange:
    def test_starts_at_the_first_internal_number(self, repo):
        assert repo.next_number() == "10000000"

    def test_continues_after_the_highest_number(self, repo):
        repo.add(requisition("10000004", item("10000004")))
        assert repo.next_number() == "10000005"


class TestStoringARequisition:
    def test_a_stored_requisition_comes_back_with_its_items_and_values(self, repo):
        stored = requisition("10000000", item("10000000", "10"), item("10000000", "20", release_codes=("01", "02"), supplier="S1", is_deleted=True))
        repo.add(stored)
        assert repo.get("10000000") == stored
        assert repo.list_all() == [stored]

    def test_an_unknown_number_is_none(self, repo):
        assert repo.get("10000009") is None

    def test_an_update_replaces_the_items(self, repo):
        repo.add(requisition("10000000", item("10000000", "10"), item("10000000", "20")))
        changed = requisition("10000000", item("10000000", "10", release_status="03", release_codes=("01",)))
        repo.update(changed)
        assert repo.get("10000000") == changed


class TestItemAmounts:
    def test_net_amount_is_quantity_times_price(self):
        assert item("1").net_amount == Decimal("200.00")

    def test_an_item_is_not_released_until_status_03(self):
        assert item("1").release_is_not_completed
        assert not item("1", release_status="03").release_is_not_completed


class TestReleaseRules:
    @pytest.mark.parametrize(
        "value, codes",
        [("99999.99", ()), ("100000", ("01",)), ("999999.99", ("01",)), ("1000000", ("01", "02"))],
    )
    def test_the_net_value_decides_the_codes(self, value, codes):
        assert rule_for("NB", "1010", Decimal(value)).release_codes == codes

    def test_a_type_without_a_rule_has_none(self):
        assert rule_for("XX", "1010", Decimal("500000"), (ReleaseRule("NB", "*", Decimal("0"), None, "", (), ()),)) is None

    def test_a_plant_rule_beats_nothing_when_the_plant_differs(self):
        rules = (ReleaseRule("NB", "2000", Decimal("0"), None, "09", ("01",), ("approver",)),) + RELEASE_RULES
        assert rule_for("NB", "1010", Decimal("5"), rules).release_group == ""
        assert rule_for("NB", "2000", Decimal("5"), rules).release_group == "09"
