from datetime import date
from decimal import Decimal

from butterfly.domain.entities.drivers import CustomerInvoice

BUCKETS = ["current", "1-30", "31-60", "61-90", "90+"]


def open_amount(invoice: CustomerInvoice, as_of: date) -> Decimal:
    if invoice.invoice_date > as_of:
        return Decimal("0.00")
    cleared = invoice.cleared_amount if invoice.clearing_date and invoice.clearing_date <= as_of else Decimal("0.00")
    return invoice.net_amount - cleared


def is_overdue(invoice: CustomerInvoice, as_of: date) -> bool:
    return invoice.due_date < as_of and open_amount(invoice, as_of) > 0


def bucket_of(invoice: CustomerInvoice, as_of: date) -> str:
    days = (as_of - invoice.due_date).days
    if days <= 0:
        return BUCKETS[0]
    if days <= 30:
        return BUCKETS[1]
    if days <= 60:
        return BUCKETS[2]
    if days <= 90:
        return BUCKETS[3]
    return BUCKETS[4]


def open_invoices(invoices: list[CustomerInvoice], as_of: date) -> list[CustomerInvoice]:
    return [invoice for invoice in invoices if open_amount(invoice, as_of) > 0]
