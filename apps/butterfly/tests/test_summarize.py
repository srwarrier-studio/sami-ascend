from decimal import Decimal

from butterfly.application.usecase.summarize_by_customer import SummarizeByCustomer
from butterfly.application.usecase.summarize_by_day import SummarizeByDay
from butterfly.application.usecase.summarize_by_material import SummarizeByMaterial
from butterfly.infrastructure.memory.in_memory_sales_order_repo import InMemorySalesOrderRepo
from conftest import ORDERS

REPO = InMemorySalesOrderRepo(ORDERS)
LIVE = [o for o in ORDERS if o.overall_status != "X"]


def live_on(day):
    return [o for o in LIVE if o.order_date == day]


class TestSummarizeByDay:
    def test_one_row_per_seed_date_in_date_order(self):
        rows = SummarizeByDay(REPO).execute()

        assert [r.order_date for r in rows] == sorted({o.order_date for o in LIVE})

    def test_each_row_sums_that_days_orders(self):
        for row in SummarizeByDay(REPO).execute():
            orders = live_on(row.order_date)
            assert row.total_net_amount == sum(o.total_net_amount for o in orders)
            assert row.order_count == len(orders)
            assert row.currency == "INR"

    def test_order_counts_add_up_to_the_orders_that_are_not_cancelled(self):
        rows = SummarizeByDay(REPO).execute()

        assert sum(r.order_count for r in rows) == len(LIVE)

    def test_cancelled_orders_are_left_out(self):
        assert any(o.overall_status == "X" for o in ORDERS)
        total = sum(r.total_net_amount for r in SummarizeByDay(REPO).execute())

        assert total == sum(o.total_net_amount for o in LIVE)

    def test_a_day_with_only_cancelled_orders_has_no_row(self):
        cancelled = [o for o in ORDERS if o.overall_status == "X"][:1]

        assert SummarizeByDay(InMemorySalesOrderRepo(cancelled)).execute() == []

    def test_empty_repo_gives_no_rows(self):
        assert SummarizeByDay(InMemorySalesOrderRepo([])).execute() == []


class TestSummarizeByCustomer:
    def test_rows_add_up_to_the_day_totals(self):
        days = {r.order_date: r for r in SummarizeByDay(REPO).execute()}
        rows = SummarizeByCustomer(REPO).execute()

        for day, summary in days.items():
            same_day = [r for r in rows if r.order_date == day]
            assert sum(r.total_net_amount for r in same_day) == summary.total_net_amount
            assert sum(r.order_count for r in same_day) == summary.order_count

    def test_one_row_per_customer_and_date_with_the_name(self):
        rows = SummarizeByCustomer(REPO).execute()
        keys = [(r.sold_to_party, r.order_date) for r in rows]

        assert len(keys) == len(set(keys))
        assert all(r.customer_name for r in rows)

    def test_rows_start_with_the_oldest_date(self):
        rows = SummarizeByCustomer(REPO).execute()

        assert [r.order_date for r in rows] == sorted(r.order_date for r in rows)


class TestSummarizeByMaterial:
    def test_amounts_add_up_to_the_day_totals(self):
        days = {r.order_date: r for r in SummarizeByDay(REPO).execute()}
        rows = SummarizeByMaterial(REPO).execute()

        for day, summary in days.items():
            same_day = [r for r in rows if r.order_date == day]
            assert sum(r.total_net_amount for r in same_day) == summary.total_net_amount

    def test_quantity_is_the_sum_of_item_quantities(self):
        row = SummarizeByMaterial(REPO).execute()[0]
        expected = sum(
            i.quantity
            for o in live_on(row.order_date)
            for i in o.items
            if i.material == row.material
        )

        assert row.total_quantity == expected
        assert row.quantity_unit

    def test_one_row_per_material_and_date(self):
        rows = SummarizeByMaterial(REPO).execute()
        keys = [(r.material, r.order_date) for r in rows]

        assert len(keys) == len(set(keys))

    def test_quantity_keeps_three_decimals_and_amount_two(self):
        row = SummarizeByMaterial(REPO).execute()[0]

        assert row.total_quantity == Decimal(str(row.total_quantity))
        assert row.total_quantity.as_tuple().exponent == -3
        assert row.total_net_amount.as_tuple().exponent == -2
