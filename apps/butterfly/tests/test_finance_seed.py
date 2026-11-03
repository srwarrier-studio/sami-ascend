from collections import Counter, defaultdict
from datetime import date, timedelta
from decimal import Decimal

from butterfly.infrastructure.memory.companies import COMPANIES
from butterfly.infrastructure.memory.finance_seed import EXPENSE_DAYS, build_cash
from butterfly.infrastructure.memory.scenarios import find_scenario
from butterfly.infrastructure.memory.story_seed import build_story_seed
from butterfly.infrastructure.sqlite.database import Database
from butterfly.infrastructure.sqlite.money import from_minor
from butterfly.infrastructure.sqlite.seeder import prepare

TODAY = date(2026, 11, 3)
STORY = build_story_seed(TODAY, find_scenario("august-contract"), COMPANIES)
CASH = build_cash(STORY.invoices, STORY.deliveries, TODAY)


def of(kind):
    return [p for p in CASH if p.payment_type == kind]


class TestCustomerPayments:
    def test_every_cleared_invoice_has_one_payment_for_exactly_the_cleared_amount(self):
        cleared = {i.invoice: i for i in STORY.invoices if i.clearing_date and i.clearing_date <= TODAY and i.cleared_amount > 0}
        paid = {p.reference: p for p in of("C")}
        assert paid.keys() == cleared.keys() and len(of("C")) == len(cleared)
        for number, payment in paid.items():
            invoice = cleared[number]
            assert (payment.amount, payment.posting_date, payment.partner, payment.company_code) == (invoice.cleared_amount_local, invoice.clearing_date, invoice.sold_to_party, invoice.company_code)
            assert (payment.document_amount, payment.document_currency) == (invoice.cleared_amount, invoice.transaction_currency)

    def test_customer_payments_come_in(self):
        assert {p.direction for p in of("C")} == {"I"}


class TestVendorPayments:
    def test_only_delivered_purchases_whose_payment_date_has_come_are_paid(self):
        delivered = {d.purchase_order: d for d in STORY.deliveries if d.delivery_status != "X" and d.actual_delivery_date}
        paid = of("V")
        assert paid and all(p.reference in delivered for p in paid)
        for p in paid:
            d = delivered[p.reference]
            assert p.posting_date <= TODAY and p.posting_date >= d.actual_delivery_date + timedelta(days=30)
            assert (p.amount, p.partner, p.direction) == (d.net_amount_local, d.supplier, "O")

    def test_a_purchase_delivered_yesterday_is_not_paid_yet(self):
        recent = {d.purchase_order for d in STORY.deliveries if d.actual_delivery_date and d.actual_delivery_date > TODAY - timedelta(days=30)}
        assert recent and not recent & {p.reference for p in of("V")}


class TestRunningCosts:
    def test_each_company_pays_six_categories_a_month_on_their_days(self):
        by_month = defaultdict(Counter)
        for p in of("E"):
            assert p.posting_date.day == EXPENSE_DAYS[p.expense_category] and p.direction == "O"
            by_month[(p.posting_date.year, p.posting_date.month, p.company_code)][p.expense_category] += 1
        assert {c for _, _, c in by_month} == {"INA1", "INA2", "INA3"}
        assert all(set(c.values()) == {1} for c in by_month.values())
        full = [c for (y, m, _), c in by_month.items() if (y, m) < (2026, 11)]
        assert all(len(c) == 6 for c in full)

    def test_costs_that_fall_after_today_are_not_posted(self):
        assert [p.expense_category for p in of("E") if p.posting_date >= date(2026, 11, 1)] == ["RENT"] * 3

    def test_a_bigger_company_pays_more(self):
        rent = {p.company_code: p.amount for p in of("E") if p.expense_category == "RENT" and p.posting_date == date(2026, 10, 1)}
        assert rent["INA1"] > rent["INA2"] > rent["INA3"]


class TestDocuments:
    def test_nothing_is_posted_after_today_and_amounts_are_positive_rupees(self):
        assert all(p.posting_date <= TODAY and p.amount > 0 and p.currency == "INR" for p in CASH)

    def test_numbers_are_unique_and_follow_the_posting_date(self):
        numbers = [p.payment_document for p in CASH]
        assert numbers == sorted(numbers) and len(set(numbers)) == len(numbers)
        assert [p.posting_date for p in CASH] == sorted(p.posting_date for p in CASH)

    def test_the_month_pays_out_roughly_what_it_brings_in(self):
        month = [p for p in CASH if date(2026, 10, 1) <= p.posting_date <= date(2026, 10, 31)]
        incoming = sum(p.amount for p in month if p.direction == "I")
        outgoing = sum(p.amount for p in month if p.direction == "O")
        assert Decimal("0.5") < outgoing / incoming < Decimal("2")


class TestStored:
    def test_the_database_holds_the_same_payments(self):
        db = Database()
        prepare(db, "story", "august-contract", TODAY, STORY)
        stored = db.query("SELECT payment_document, amount FROM cash_payment ORDER BY payment_document")
        assert [(r["payment_document"], from_minor(r["amount"])) for r in stored] == [(p.payment_document, p.amount) for p in CASH]

    def test_the_small_seed_has_no_payments(self):
        db = Database()
        prepare(db, "small", "august-contract", TODAY, None)
        assert db.query("SELECT COUNT(*) AS n FROM cash_payment")[0]["n"] == 0
