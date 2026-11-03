from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from butterfly.domain.entities.drivers import CustomerInvoice, PurchaseDelivery
from butterfly.domain.entities.finance import CashPayment

CURRENCY = "INR"
MONEY = Decimal("0.01")
VENDOR_DAYS = 30
VENDOR_DAYS_USD = 45
VENDOR_DELAY_SPREAD = 6
EXPENSE_DAYS = {"RENT": 1, "UTILITIES": 10, "FREIGHT": 15, "MAINTENANCE": 20, "MARKETING": 22, "SALARIES": 25}
EXPENSE_BASE = {"SALARIES": 720000, "RENT": 90000, "UTILITIES": 75000, "FREIGHT": 270000, "MAINTENANCE": 105000, "MARKETING": 120000}
COMPANY_SCALE = {"INA1": Decimal("1.0"), "INA2": Decimal("0.8"), "INA3": Decimal("0.6")}
TYPE_ORDER = {"C": 0, "V": 1, "E": 2}
DIRECTION = {"C": "I", "V": "O", "E": "O"}


@dataclass(frozen=True)
class Event:
    day: date
    kind: str
    company: str
    partner: str | None
    name: str | None
    category: str | None
    reference: str | None
    amount: Decimal
    document_amount: Decimal
    document_currency: str


def customer_events(invoices: list[CustomerInvoice], today: date) -> list[Event]:
    return [
        Event(i.clearing_date, "C", i.company_code, i.sold_to_party, i.customer_name, None, i.invoice, i.cleared_amount_local, i.cleared_amount, i.transaction_currency)
        for i in invoices
        if i.clearing_date is not None and i.clearing_date <= today and i.cleared_amount > 0
    ]


def vendor_events(deliveries: list[PurchaseDelivery], today: date) -> list[Event]:
    events = []
    for d in deliveries:
        if d.delivery_status == "X" or d.actual_delivery_date is None:
            continue
        terms = VENDOR_DAYS_USD if d.transaction_currency == "USD" else VENDOR_DAYS
        paid = d.actual_delivery_date + timedelta(days=terms + int(d.purchase_order) % VENDOR_DELAY_SPREAD)
        if paid <= today:
            events.append(Event(paid, "V", d.company_code, d.supplier, d.supplier_name, None, d.purchase_order, d.net_amount_local, d.net_amount, d.transaction_currency))
    return events


def expense_events(first: date, today: date) -> list[Event]:
    events = []
    index = first.year * 12 + first.month - 1
    while index <= today.year * 12 + today.month - 1:
        year, month = index // 12, index % 12 + 1
        for company, scale in COMPANY_SCALE.items():
            for category, day in EXPENSE_DAYS.items():
                posted = date(year, month, day)
                if posted > today:
                    continue
                variation = 1 + Decimal((index * 7 + sum(map(ord, category + company))) % 9 - 4) / 100
                amount = (EXPENSE_BASE[category] * scale * variation).quantize(MONEY)
                events.append(Event(posted, "E", company, None, None, category, None, amount, amount, CURRENCY))
        index += 1
    return events


def build_cash(invoices: list[CustomerInvoice], deliveries: list[PurchaseDelivery], today: date) -> list[CashPayment]:
    first = min([i.invoice_date for i in invoices] + [d.order_date for d in deliveries], default=today).replace(day=1)
    events = sorted(
        [*customer_events(invoices, today), *vendor_events(deliveries, today), *expense_events(first, today)],
        key=lambda e: (e.day, TYPE_ORDER[e.kind], e.company, e.category or "", e.reference or ""),
    )
    return [
        CashPayment(
            f"{1500000000 + number:010d}", e.day, DIRECTION[e.kind], e.kind, e.partner, e.name, e.category, e.reference, e.amount, CURRENCY, e.document_amount, e.document_currency, e.company,
        )
        for number, e in enumerate(events, start=1)
    ]
