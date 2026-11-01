from datetime import date, timedelta
from decimal import Decimal

from fastapi.testclient import TestClient

from butterfly.entrypoint.app import build_default_app
from butterfly.infrastructure.api.odata import DRIVERS_ROOT
from butterfly.infrastructure.memory.story_seed import build_story_seed

TODAY = date(2026, 10, 31)
SEED = build_story_seed(TODAY)
ORDERS = {order.sales_order: order for order in SEED.orders}
INVOICES = {invoice.invoice: invoice for invoice in SEED.invoices}
TERMS = {"0000100001": 30, "0000100002": 45, "0000100003": 60, "0000100004": 30, "0000100005": 45}


def invoice_of(order):
    return INVOICES["9" + order.sales_order[1:]]


class TestInvoicesFollowTheSalesOrders:
    def test_every_order_that_is_not_cancelled_has_one_invoice(self):
        billed = [order for order in SEED.orders if order.overall_status != "X"]
        assert len(SEED.invoices) == len(INVOICES) == len(billed)

    def test_a_cancelled_order_has_no_invoice(self):
        cancelled = next(order for order in SEED.orders if order.overall_status == "X")
        assert "9" + cancelled.sales_order[1:] not in INVOICES

    def test_customer_date_and_amount_come_from_the_order(self):
        for order in SEED.orders:
            if order.overall_status == "X":
                continue
            invoice = invoice_of(order)
            assert (invoice.sold_to_party, invoice.customer_name, invoice.invoice_date) == (order.sold_to_party, order.customer_name, order.order_date)
            assert (invoice.net_amount, invoice.transaction_currency) == (order.total_net_amount, order.transaction_currency)

    def test_the_due_date_adds_the_payment_terms_of_the_customer(self):
        for invoice in SEED.invoices:
            assert invoice.due_date - invoice.invoice_date == timedelta(days=TERMS[invoice.sold_to_party])


class TestPayments:
    def test_an_invoice_is_cleared_in_full_or_not_at_all(self):
        for invoice in SEED.invoices:
            assert invoice.cleared_amount in (invoice.net_amount, Decimal("0.00"))
            assert (invoice.clearing_date is not None) == (invoice.cleared_amount == invoice.net_amount)

    def test_nothing_clears_after_today(self):
        assert all(invoice.clearing_date <= TODAY for invoice in SEED.invoices if invoice.clearing_date)

    def test_a_prompt_payer_clears_on_the_due_date(self):
        old = next(i for i in SEED.invoices if i.sold_to_party == "0000100001" and i.due_date < TODAY)
        assert old.clearing_date == old.due_date

    def test_a_slow_payer_pays_75_days_after_the_due_date(self):
        old = next(i for i in SEED.invoices if i.sold_to_party == "0000100003" and i.clearing_date)
        assert old.clearing_date - old.due_date == timedelta(days=75)

    def test_the_customer_who_never_pays_keeps_every_invoice_open(self):
        mine = [i for i in SEED.invoices if i.sold_to_party == "0000100005"]
        assert mine and all(i.clearing_date is None for i in mine)

    def test_some_invoices_are_open_and_past_due(self):
        assert any(i.clearing_date is None and i.due_date < TODAY for i in SEED.invoices)


class TestInvoiceRoute:
    client = TestClient(build_default_app(TODAY))

    def test_lists_the_invoices_with_the_contract_fields(self):
        body = self.client.get(DRIVERS_ROOT + "CustomerInvoice?$top=1").json()
        assert body["@odata.context"] == "$metadata#CustomerInvoice"
        assert set(body["value"][0]) == {"Invoice", "SoldToParty", "CustomerName", "InvoiceDate", "DueDate", "NetAmount", "TransactionCurrency", "ClearedAmount", "ClearingDate", "CompanyCode"}

    def test_filters_and_counts_like_the_other_entities(self):
        body = self.client.get(DRIVERS_ROOT + "CustomerInvoice?$filter=SoldToParty eq '0000100005'&$count=true&$top=1").json()
        assert body["@odata.count"] == len([i for i in SEED.invoices if i.sold_to_party == "0000100005"])
