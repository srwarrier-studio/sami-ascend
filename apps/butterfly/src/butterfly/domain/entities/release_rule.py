from dataclasses import dataclass, replace
from decimal import Decimal

from butterfly.domain.entities.master_data import to_local
from butterfly.domain.entities.purchase_requisition import NOT_RELEASED, RELEASED, PurchaseRequisitionItem


@dataclass(frozen=True)
class ReleaseRule:
    requisition_type: str
    plant: str
    value_from: Decimal
    value_to: Decimal | None
    release_group: str
    release_codes: tuple[str, ...]
    approver_roles: tuple[str, ...]

    def applies_to(self, requisition_type: str, plant: str, value: Decimal) -> bool:
        return (
            self.requisition_type in (requisition_type, "*")
            and self.plant in (plant, "*")
            and value >= self.value_from
            and (self.value_to is None or value < self.value_to)
        )


RELEASE_RULES = (
    ReleaseRule("NB", "*", Decimal("0"), Decimal("100000"), "", (), ()),
    ReleaseRule("NB", "*", Decimal("100000"), Decimal("1000000"), "01", ("01",), ("approver",)),
    ReleaseRule("NB", "*", Decimal("1000000"), None, "02", ("01", "02"), ("approver", "approver")),
)


def rule_for(requisition_type: str, plant: str, value: Decimal, rules: tuple[ReleaseRule, ...] = RELEASE_RULES) -> ReleaseRule | None:
    return next((rule for rule in rules if rule.applies_to(requisition_type, plant, value)), None)


def rule_of_item(item: PurchaseRequisitionItem, requisition_type: str, rules: tuple[ReleaseRule, ...] = RELEASE_RULES) -> ReleaseRule | None:
    return rule_for(requisition_type, item.plant, to_local(item.net_amount, item.currency), rules)


def with_release_status(item: PurchaseRequisitionItem, requisition_type: str, rules: tuple[ReleaseRule, ...] = RELEASE_RULES) -> PurchaseRequisitionItem:
    rule = rule_of_item(item, requisition_type, rules)
    released = rule is None or not rule.release_codes
    return replace(item, release_status=RELEASED if released else NOT_RELEASED, release_codes=())
