from dataclasses import dataclass
from decimal import Decimal


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
