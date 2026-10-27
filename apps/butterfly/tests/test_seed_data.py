from butterfly.infrastructure.memory.seed import ORDER_COUNT, build_seed
from conftest import ORDERS, TODAY


class TestSeedData:
    def test_same_day_gives_the_same_orders(self):
        assert build_seed(TODAY) == ORDERS

    def test_has_thirty_orders(self):
        assert len(ORDERS) == ORDER_COUNT

    def test_covers_all_four_statuses(self):
        assert {order.overall_status for order in ORDERS} == {"A", "B", "C", "X"}

    def test_latest_order_is_today(self):
        assert max(order.order_date for order in ORDERS) == TODAY

    def test_every_order_has_two_or_three_items(self):
        assert all(2 <= len(order.items) <= 3 for order in ORDERS)

    def test_order_total_is_the_sum_of_its_items(self):
        for order in ORDERS:
            assert order.total_net_amount == sum(item.net_amount for item in order.items)

    def test_some_orders_have_no_requested_delivery_date(self):
        assert any(order.requested_delivery_date is None for order in ORDERS)
