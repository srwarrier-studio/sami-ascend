# butterfly/20 finance-cash

## Goal
Butterfly serves cash as SAP will: a read-only OData V4 service `ZUI_FINANCE_O4` with cleared payments (money in from customers, money out to vendors and for running costs) and two summaries, specified in `docs/sap/finance-contract.md`, with payments that follow from the invoices, the purchases and a monthly cost pattern.

## Why
The five Finance cash widgets (collections, collection target, cash in and out, recent payments, expenses by category) are the last widgets on fixed numbers in synapse-api's `mock_library.json`. Collections can be read from invoices that were cleared; vendor payments and running costs need payments that butterfly does not have yet.

## Behavior
- **Contract first.** `docs/sap/finance-contract.md` (written with this spec) defines the service, `CashPayment` and the summaries `CashSummaryByDay` and `ExpenseSummaryByDay`, with fields, codes, joins and SAP sources. Consultant questions 40 to 45 are in `consultant-questions.md`. Every example is a real response checked by a test.
- **Same conventions** as the other services; the summaries are SQL views; amounts are in rupees with the document amount alongside, like exports.
- **One story**, generated with the document flow (so orders created through the API produce payments as their invoices clear):
  - **Customer payments (`C`, in):** one for each invoice cleared up to today, on the clearing date, for the cleared amount (rupees and document currency).
  - **Vendor payments (`V`, out):** one for each purchase that was delivered and not cancelled, 30 days after the delivery (45 for a dollar vendor), plus a small deterministic delay, once that date has come.
  - **Running costs (`E`, out):** every company posts the six cost categories each month on fixed days (rent on the 1st, utilities on the 10th, freight on the 15th, maintenance on the 20th, marketing on the 22nd, salaries on the 25th), with amounts scaled by company and a small monthly variation, up to today.
  - Payment documents are numbered in posting order; everything is deterministic for a seed and today's date.
- **Tables and views.** New table `cash_payment` (written with the derived documents), two `.sql` views; an older database is upgraded (the new table is created at start and filled by the layout rebuild).
- The document flow recomputes payments after every order write, so a created order's invoice becomes a customer payment when it clears.
- Nothing already served changes.

## Acceptance cases
- Customer payments equal the cleared invoices exactly (same invoice, date, amounts); no uncleared invoice has a payment.
- Vendor payments cover exactly the delivered, non-cancelled purchase items whose payment date has come; each pays the item's rupee amount.
- Each company has all six cost categories in each month up to today, on their days, in rupees; no payment is dated after today.
- Direction and type codes agree (`C` is `I`; `V` and `E` are `O`); numbers are unique and follow posting order.
- `CashSummaryByDay` and `ExpenseSummaryByDay` equal hand totals over the payments, for a `CompanyCode` filter too; the database and the lists answer the same for filters, ordering and paging.
- Create an order through the API with a customer who pays quickly enough to clear on a day up to today: the payment appears; one that clears later has none.
- `BUTTERFLY_SEED=small` serves no payments; an older database is upgraded and keeps API orders.

## Out of scope
The synapse-api widgets (synapse-api 17), bank accounts and balances, partial payments, payment runs, taxes and payroll detail, writes, authentication.

## Depends on
butterfly 19 (rupee amounts, in-place upgrade; branch base), butterfly 18 (document flow).
