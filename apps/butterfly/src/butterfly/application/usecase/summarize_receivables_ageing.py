from datetime import date
from decimal import Decimal

from butterfly.application.receivables import BUCKETS, bucket_of, open_amount, open_invoices
from butterfly.domain.entities.sales_summary import ReceivablesAgeing
from butterfly.domain.repositories.driver_repo import DriverRepo


class SummarizeReceivablesAgeing:
    def __init__(self, repo: DriverRepo):
        self.repo = repo

    def execute(self, as_of: date) -> list[ReceivablesAgeing]:
        totals: dict[tuple, list] = {}
        for invoice in open_invoices(self.repo.invoices(), as_of):
            entry = totals.setdefault((invoice.transaction_currency, BUCKETS.index(bucket_of(invoice, as_of))), [Decimal("0.00"), 0])
            entry[0] += open_amount(invoice, as_of)
            entry[1] += 1
        return [ReceivablesAgeing(as_of, BUCKETS[bucket], amount, count, currency) for (currency, bucket), (amount, count) in sorted(totals.items())]
