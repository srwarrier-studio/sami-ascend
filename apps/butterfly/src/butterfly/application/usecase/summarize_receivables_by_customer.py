from datetime import date
from decimal import Decimal

from butterfly.application.receivables import is_overdue, open_amount, open_invoices
from butterfly.domain.entities.sales_summary import ReceivablesByCustomer
from butterfly.domain.repositories.driver_repo import DriverRepo


class SummarizeReceivablesByCustomer:
    def __init__(self, repo: DriverRepo):
        self.repo = repo

    def execute(self, as_of: date) -> list[ReceivablesByCustomer]:
        totals: dict[tuple, list] = {}
        for invoice in open_invoices(self.repo.invoices(), as_of):
            entry = totals.setdefault((invoice.sold_to_party, invoice.transaction_currency, invoice.company_code), [invoice.customer_name, Decimal("0.00"), Decimal("0.00"), 0, 0])
            entry[1] += open_amount(invoice, as_of)
            entry[3] += 1
            if is_overdue(invoice, as_of):
                entry[2] += open_amount(invoice, as_of)
                entry[4] += 1
        return [
            ReceivablesByCustomer(customer, name, as_of, open_total, overdue_total, open_count, overdue_count, currency, company)
            for (customer, currency, company), (name, open_total, overdue_total, open_count, overdue_count) in sorted(totals.items())
        ]
