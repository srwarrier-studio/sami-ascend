import pytest

from butterfly.domain.entities.number_range import MATERIAL_DOCUMENT, PURCHASE_ORDER, PURCHASE_REQUISITION, NumberRange
from butterfly.domain.errors import NumberRangeFull


class TestNext:
    def test_the_first_number_of_an_empty_range_is_its_start(self):
        assert PURCHASE_REQUISITION.next([]) == "10000000"

    def test_the_number_after_the_highest_taken_is_given(self):
        assert PURCHASE_ORDER.next(["4500000011", "4500000012"]) == "4500000013"

    def test_a_gap_is_never_filled(self):
        assert PURCHASE_ORDER.next(["4500000001", "4500000009"]) == "4500000010"

    def test_numbers_below_the_range_are_ignored(self):
        assert PURCHASE_REQUISITION.next(["5"]) == "10000000"

    def test_a_full_range_refuses(self):
        with pytest.raises(NumberRangeFull):
            NumberRange(1, 3).next(["3"])


class TestYears:
    def test_year_dependent_ranges_are_marked(self):
        assert MATERIAL_DOCUMENT.per_year and not PURCHASE_ORDER.per_year

    def test_the_same_number_restarts_in_a_new_year(self):
        taken_in_2016 = ["4900000121"]
        assert MATERIAL_DOCUMENT.next(taken_in_2016) == "4900000122"
        assert MATERIAL_DOCUMENT.next([]) == "4900000000"


class TestTheNextNumbersOfTheRepositories:
    def test_the_first_requisition_is_the_start_of_its_range_and_the_next_follows_the_highest(self):
        from butterfly.infrastructure.memory.in_memory_purchase_requisition_repo import InMemoryPurchaseRequisitionRepo

        repo = InMemoryPurchaseRequisitionRepo()
        assert repo.next_number() == "10000000"
        repo.requisitions["10000007"] = object()
        assert repo.next_number() == "10000008"

    def test_the_next_sales_order_is_kept_in_its_ten_digit_stored_form(self):
        from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo

        repo = InMemorySalesOrderRepo([])
        assert repo.next_number() == "0000000001"
        repo.orders["0000012001"] = object()
        assert repo.next_number() == "0000012002"
