from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from butterfly.domain.entities.drivers import PurchaseDelivery
from butterfly.domain.entities.purchase_order import PurchaseOrder, PurchaseOrderItem
from butterfly.infrastructure.memory.in_memory_driver_repo import InMemoryDriverRepo
from butterfly.infrastructure.memory.in_memory_purchase_order_repo import InMemoryPurchaseOrderRepo
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.purchase_order_repo import SqlitePurchaseOrderRepo

NOW = datetime(2026, 11, 4, 10, 0)


def delivery(number: str, line: str = "00010", status: str = "O") -> PurchaseDelivery:
    return PurchaseDelivery(
        number, line, "S1", "Herb Traders", "MZ-TG-A11", "Battery", date(2026, 11, 4), Decimal("10.000"), Decimal("0.000"), "PC",
        date(2026, 12, 1), None, status, Decimal("200.00"), "INR", "INA1",
    )


def order(number: str, *lines: str) -> PurchaseOrder:
    items = [PurchaseOrderItem(delivery(number, line), "1010", "10000001", "00010") for line in lines]
    return PurchaseOrder(number, "NB", "INA1", "1010", "002", "S1", "INR", "purchase1", NOW, NOW, items)


@pytest.fixture(params=["memory", "sqlite"])
def repo(request):
    if request.param == "memory":
        return InMemoryPurchaseOrderRepo(InMemoryDriverRepo())
    return SqlitePurchaseOrderRepo(Database())


class TestNumberRange:
    def test_starts_at_the_first_internal_number(self, repo):
        assert repo.next_number() == "4500000001"

    def test_continues_after_the_highest_number(self, repo):
        repo.add(order("4500000007", "00010"))
        assert repo.next_number() == "4500000008"


class TestStoringAnOrder:
    def test_a_stored_order_comes_back_with_its_items_and_links(self, repo):
        stored = order("4500000001", "00010", "00020")
        repo.add(stored)
        assert repo.get("4500000001") == stored

    def test_an_unknown_order_is_not_found(self, repo):
        assert repo.get("4500000099") is None

    def test_orders_are_listed_in_the_order_they_were_added(self, repo):
        repo.add(order("4500000002", "00010"))
        repo.add(order("4500000001", "00010"))
        assert [o.purchase_order for o in repo.list_all()] == ["4500000002", "4500000001"]


class TestCancellingAnItem:
    def test_the_item_is_cancelled_and_the_other_stays(self, repo):
        repo.add(order("4500000001", "00010", "00020"))
        later = datetime(2026, 11, 5, 9, 0)
        repo.cancel_item("4500000001", "00010", later)
        stored = repo.get("4500000001")
        assert [i.is_cancelled for i in stored.items] == [True, False]
        assert stored.last_change_date_time == later


class TestOrdersThatWereSeeded:
    def test_a_seeded_delivery_is_an_order_without_a_header(self):
        drivers = InMemoryDriverRepo(deliveries=[delivery("4500000050")])
        seeded = InMemoryPurchaseOrderRepo(drivers).get("4500000050")
        assert (seeded.order_type, seeded.supplier, seeded.items[0].purchase_requisition) == ("NB", "S1", "")
