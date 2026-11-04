from dataclasses import replace
from datetime import datetime, timedelta, timezone
from typing import Callable

from butterfly.application.usecase.change_purchase_requisition_item import RequisitionNotFound
from butterfly.application.usecase.create_sales_order import utc_now
from butterfly.domain.entities.purchase_requisition import IN_RELEASE, RELEASED, PurchaseRequisition, PurchaseRequisitionItem
from butterfly.domain.entities.release_rule import RELEASE_RULES, ReleaseRule, rule_of_item
from butterfly.domain.errors import ValidationDetail, ValidationFailed
from butterfly.domain.repositories.purchase_requisition_repo import PurchaseRequisitionRepo


class ReleasePurchaseRequisition:
    def __init__(self, repo: PurchaseRequisitionRepo, now: Callable[[], datetime] = utc_now, rules: tuple[ReleaseRule, ...] = RELEASE_RULES):
        self.repo = repo
        self.now = now
        self.rules = rules

    def execute(self, number: str, code: str, item_number: str | None = None) -> PurchaseRequisition:
        requisition = self.repo.get(number)
        if requisition is None:
            raise RequisitionNotFound(number)
        targets = [i for i in requisition.items if item_number is None or i.purchase_requisition_item == item_number]
        if item_number is not None and not targets:
            raise RequisitionNotFound(f"{number}/{item_number}")
        problems = []
        changed = {}
        for item in targets:
            reason = self.refusal(item, requisition.requisition_type, code)
            if reason is None:
                changed[item.purchase_requisition_item] = self.given(item, code, requisition.requisition_type)
            else:
                problems.append(ValidationDetail("RELEASE_REFUSED", f"Item {item.purchase_requisition_item}: {reason}", "ReleaseCode"))
        if item_number is not None and problems or not changed:
            raise ValidationFailed(problems or [ValidationDetail("RELEASE_REFUSED", "There is nothing to release.", "ReleaseCode")])
        moment = self.now().astimezone(timezone.utc).replace(microsecond=0)
        items = [changed.get(i.purchase_requisition_item, i) for i in requisition.items]
        saved = replace(requisition, items=items, last_change_date_time=max(moment, requisition.last_change_date_time + timedelta(seconds=1)))
        self.repo.update(saved)
        return saved

    def chain(self, item: PurchaseRequisitionItem, requisition_type: str) -> tuple[str, ...]:
        rule = rule_of_item(item, requisition_type, self.rules)
        return rule.release_codes if rule else ()

    def refusal(self, item: PurchaseRequisitionItem, requisition_type: str, code: str) -> str | None:
        chain = self.chain(item, requisition_type)
        if item.is_deleted:
            return "the item is deleted."
        if item.release_status == RELEASED:
            return "the item is already released."
        if code in item.release_codes:
            return f"release code {code} was already given."
        if len(item.release_codes) >= len(chain) or chain[len(item.release_codes)] != code:
            return f"release code {code} is not the next code in the release strategy."
        return None

    def given(self, item: PurchaseRequisitionItem, code: str, requisition_type: str) -> PurchaseRequisitionItem:
        codes = item.release_codes + (code,)
        done = len(codes) == len(self.chain(item, requisition_type))
        return replace(item, release_codes=codes, release_status=RELEASED if done else IN_RELEASE)
