from datetime import date
from decimal import Decimal

from butterfly.application.receivables import is_overdue, open_amount, open_invoices
from butterfly.domain.entities.master_data import to_local
from butterfly.domain.entities.sales_summary import ReceivablesByCustomer
from butterfly.domain.repositories.driver_repo import DriverRepo

ZERO = Decimal("0.00")


class SummarizeReceivablesByCustomer:
    def __init__(self, repo: DriverRepo):
        self.repo = repo

    def execute(self, as_of: date) -> list[ReceivablesByCustomer]:
        totals: dict[tuple, list] = {}
        for invoice in open_invoices(self.repo.invoices(), as_of):
            entry = totals.setdefault((invoice.sold_to_party, invoice.transaction_currency, invoice.company_code), [invoice.customer_name, ZERO, ZERO, 0, 0, ZERO, ZERO])
            open_ = open_amount(invoice, as_of)
            local = to_local(open_, invoice.transaction_currency)
            entry[1] += open_
            entry[3] += 1
            entry[5] += local
            if is_overdue(invoice, as_of):
                entry[2] += open_
                entry[4] += 1
                entry[6] += local
        return [
            ReceivablesByCustomer(customer, name, as_of, open_total, overdue_total, open_count, overdue_count, currency, company, open_local, overdue_local)
            for (customer, currency, company), (name, open_total, overdue_total, open_count, overdue_count, open_local, overdue_local) in sorted(totals.items())
        ]
