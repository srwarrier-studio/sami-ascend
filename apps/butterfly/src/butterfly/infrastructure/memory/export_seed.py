from datetime import date, timedelta
from decimal import Decimal

from butterfly.domain.entities.exports import ExportShipment
from butterfly.domain.entities.master_data import USD_DIVISOR
from butterfly.domain.entities.sales_order import SalesOrder
from butterfly.infrastructure.memory.export_master import COUNTRY_NAMES, HOME
from butterfly.infrastructure.memory.story_seed import StorySeed

CURRENCY = "INR"
MONEY = Decimal("0.01")
SEA, AIR, ROAD = "S", "A", "R"
TRANSIT = {SEA: (18, 15), AIR: (3, 4), ROAD: (4, 5)}
DELAYED_EVERY = 7


def mode_of(number: int) -> str:
    share = number % 20
    return SEA if share < 12 else AIR if share < 17 else ROAD


def shipped_on(order: SalesOrder) -> date:
    return order.requested_delivery_date or order.order_date


def build_exports(story: StorySeed, today: date) -> list[ExportShipment]:
    orders = sorted(
        (order for order in story.orders if order.overall_status != "X" and order.country != HOME and shipped_on(order) <= today),
        key=lambda order: (shipped_on(order), order.sales_order),
    )
    shipments = []
    for sequence, order in enumerate(orders, start=1):
        number = int(order.sales_order)
        mode = mode_of(number)
        base, spread = TRANSIT[mode]
        shipped = shipped_on(order)
        expected = shipped + timedelta(days=base + number * 7 % spread)
        late = 1 + number % 3 if number % DELAYED_EVERY == 0 else 0
        arrival = expected + timedelta(days=late)
        rate = USD_DIVISOR if order.transaction_currency == "USD" else 1
        shipments.append(
            ExportShipment(
                f"{6000000000 + sequence:010d}", order.sales_order, order.sold_to_party, order.customer_name, order.country, COUNTRY_NAMES.get(order.country, order.country),
                mode, shipped, expected, arrival if arrival <= today else None, "D" if arrival <= today else "T", (order.total_net_amount * rate).quantize(MONEY),
                CURRENCY, order.total_net_amount, order.transaction_currency, order.company_code,
            )
        )
    return shipments
