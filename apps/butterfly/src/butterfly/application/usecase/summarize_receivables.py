from datetime import date
from decimal import Decimal

from butterfly.application.receivables import is_overdue, open_amount, open_invoices
from butterfly.domain.entities.sales_summary import ReceivablesSummary
from butterfly.domain.repositories.driver_repo import DriverRepo


class SummarizeReceivables:
    def __init__(self, repo: DriverRepo):
        self.repo = repo

    def execute(self, as_of: date) -> list[ReceivablesSummary]:
        totals: dict[tuple, list] = {}
        for invoice in open_invoices(self.repo.invoices(), as_of):
            entry = totals.setdefault((invoice.transaction_currency, invoice.company_code), [Decimal("0.00"), Decimal("0.00"), 0, 0])
            entry[0] += open_amount(invoice, as_of)
            entry[2] += 1
            if is_overdue(invoice, as_of):
                entry[1] += open_amount(invoice, as_of)
                entry[3] += 1
        return [ReceivablesSummary(as_of, *entry, *key) for key, entry in sorted(totals.items())]
