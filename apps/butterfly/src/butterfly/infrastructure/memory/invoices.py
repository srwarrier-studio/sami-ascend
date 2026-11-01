from datetime import date, timedelta
from decimal import Decimal

from butterfly.domain.entities.drivers import CustomerInvoice
from butterfly.domain.entities.sales_order import SalesOrder

PAYMENT_TERMS_DAYS = {
    "0000100001": 30,
    "0000100002": 45,
    "0000100003": 60,
    "0000100004": 30,
    "0000100005": 45,
}

PAYMENT_DELAY_DAYS = {
    "0000100001": 0,
    "0000100002": 20,
    "0000100003": 75,
    "0000100004": 10,
    "0000100005": 1000,
}


def build_invoices(orders: list[SalesOrder], today: date) -> list[CustomerInvoice]:
    return [build_invoice(order, today) for order in orders if order.overall_status != "X"]


def build_invoice(order: SalesOrder, today: date) -> CustomerInvoice:
    due = order.order_date + timedelta(days=PAYMENT_TERMS_DAYS[order.sold_to_party])
    paid_on = due + timedelta(days=PAYMENT_DELAY_DAYS[order.sold_to_party])
    cleared = paid_on <= today
    return CustomerInvoice(
        invoice="9" + order.sales_order[1:],
        sold_to_party=order.sold_to_party,
        customer_name=order.customer_name,
        invoice_date=order.order_date,
        due_date=due,
        net_amount=order.total_net_amount,
        transaction_currency=order.transaction_currency,
        cleared_amount=order.total_net_amount if cleared else Decimal("0.00"),
        clearing_date=paid_on if cleared else None,
        company_code=order.company_code,
    )
