from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class CashPayment:
    payment_document: str
    posting_date: date
    direction: str
    payment_type: str
    partner: str | None
    partner_name: str | None
    expense_category: str | None
    reference: str | None
    amount: Decimal
    currency: str
    document_amount: Decimal
    document_currency: str
    company_code: str


@dataclass(frozen=True)
class CashSummaryByDay:
    posting_date: date
    direction: str
    payment_count: int
    amount: Decimal
    currency: str
    company_code: str


@dataclass(frozen=True)
class ExpenseSummaryByDay:
    posting_date: date
    expense_category: str
    payment_count: int
    amount: Decimal
    currency: str
    company_code: str
