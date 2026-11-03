from datetime import date
from decimal import Decimal

from butterfly.application.receivables import is_overdue, open_amount, open_invoices
from butterfly.domain.entities.master_data import to_local
from butterfly.domain.entities.sales_summary import ReceivablesSummary
from butterfly.domain.repositories.driver_repo import DriverRepo

ZERO = Decimal("0.00")


class SummarizeReceivables:
    def __init__(self, repo: DriverRepo):
        self.repo = repo

    def execute(self, as_of: date) -> list[ReceivablesSummary]:
        totals: dict[tuple, list] = {}
        for invoice in open_invoices(self.repo.invoices(), as_of):
            entry = totals.setdefault((invoice.transaction_currency, invoice.company_code), [ZERO, ZERO, 0, 0, ZERO, ZERO])
            open_ = open_amount(invoice, as_of)
            local = to_local(open_, invoice.transaction_currency)
            entry[0] += open_
            entry[2] += 1
            entry[4] += local
            if is_overdue(invoice, as_of):
                entry[1] += open_
                entry[3] += 1
                entry[5] += local
        return [ReceivablesSummary(as_of, entry[0], entry[1], entry[2], entry[3], currency, company, entry[4], entry[5]) for (currency, company), entry in sorted(totals.items())]
