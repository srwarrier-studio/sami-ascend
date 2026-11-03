# Finance (cash) OData V4 contract

Source of truth for butterfly (mock SAP), the synapse gateways and the SAP consultant for cash:
what came in from customers, what went out to vendors and for running costs, and what the costs
were. If this file and any other document disagree, this file wins. Everything here is read-only.
Open receivables are in `drivers-contract.md`.

Types, `$filter` literals, `$select`, `$orderby`, `$top`, `$skip`, `$count` and the error format are
exactly as in `sales-contract.md` (sections 3, 4 and 7). `$expand` is not supported. A summary takes
the same query options as any other entity and needs the whole key in `$orderby` when paged.

## 1. Service

| Item | Value |
|------|-------|
| Service definition / binding | `ZUI_FINANCE_O4` (OData V4, UI-less web API) |
| Root path | `/sap/opu/odata4/sap/zui_finance_o4/srvd_a2x/sap/zfinance/0001/` |
| Format | JSON only (`Accept: application/json`) |

All paths below are relative to the root. Reads are `GET {root}<Entity>` with query options; reading
one row by key is not supported.

## 2. Entities

Nullable `No` means the field is always present in responses. Amounts are in the company code
currency (`Currency`, rupees) so incoming and outgoing payments in different currencies can be added;
the amount in the currency of the document is in `DocumentAmount` and `DocumentCurrency`.

### CashPayment (key: `PaymentDocument`)

One row per cleared payment: a customer payment that cleared an invoice, a vendor payment that cleared a
purchase, or a payment of a running cost. Payments that are not cleared yet are not listed.

| Field | Type | Nullable | Example |
|-------|------|----------|---------|
| `PaymentDocument` | `Edm.String` (10) | No | `"1500001234"` |
| `PostingDate` | `Edm.Date` | No | `"2026-10-28"` |
| `Direction` | `Edm.String` (1) | No | `"I"` |
| `PaymentType` | `Edm.String` (1) | No | `"C"` |
| `Partner` | `Edm.String` (10) | Yes | `"0000100001"` |
| `PartnerName` | `Edm.String` (80) | Yes | `"Harborline Nutrition LLC"` |
| `ExpenseCategory` | `Edm.String` (12) | Yes | `"SALARIES"` |
| `Reference` | `Edm.String` (10) | Yes | `"9000012001"` |
| `Amount` | `Edm.Decimal` (15,2) | No | `"2480000.00"` |
| `Currency` | `Edm.String` (5) | No | `"INR"` |
| `DocumentAmount` | `Edm.Decimal` (15,2) | No | `"31000.00"` |
| `DocumentCurrency` | `Edm.String` (5) | No | `"USD"` |
| `CompanyCode` | `Edm.String` (4) | No | `"INA1"` |

`Reference` is the invoice number for a customer payment, the purchase order for a vendor payment and
empty for a running cost. `Partner` and `PartnerName` are empty for a running cost, and
`ExpenseCategory` is empty for a customer or vendor payment. `Amount` is never negative.

### Summaries (read-only)

Aggregated by SAP so a consumer never pages through payments to total them. Amounts are in `Currency`.

| Entity | Key | Fields besides the key | Built from |
|--------|-----|------------------------|------------|
| `CashSummaryByDay` | `PostingDate`, `Direction`, `Currency`, `CompanyCode` | `PaymentCount`, `Amount` | `CashPayment` |
| `ExpenseSummaryByDay` | `PostingDate`, `ExpenseCategory`, `Currency`, `CompanyCode` | `PaymentCount`, `Amount` | `CashPayment` of type `E` |

`Amount` is `Edm.Decimal` (15,2); `PaymentCount` is `Edm.Int32`. `ExpenseSummaryByDay` has no row for
a day without running costs.

## 3. Codes

| Field | Value | Meaning |
|-------|-------|---------|
| `Direction` | `I` | Incoming: money received |
| | `O` | Outgoing: money paid |
| `PaymentType` | `C` | Customer payment (clears an invoice) |
| | `V` | Vendor payment (clears a purchase) |
| | `E` | Payment of a running cost |
| `ExpenseCategory` | `SALARIES` | Salaries and wages |
| | `RENT` | Rent |
| | `UTILITIES` | Power, water and communication |
| | `FREIGHT` | Freight and handling |
| | `MAINTENANCE` | Repairs and maintenance |
| | `MARKETING` | Marketing and selling costs |

A customer payment (`C`) is always `I`; a vendor payment (`V`) and a running cost (`E`) are always `O`.
Filter and compare codes as written.

## 4. How the entities connect

| From | To | Join |
|------|----|------|
| `CashPayment.Reference` (type `C`) | `CustomerInvoice.Invoice` | the invoice cleared; `Amount` is the cleared amount in rupees and `PostingDate` the `ClearingDate` (`drivers-contract.md`) |
| `CashPayment.Reference` (type `V`) | `PurchaseDelivery.PurchaseOrder` | the purchase paid, after the delivery (`drivers-contract.md`) |
| `CashPayment.Partner` | `SalesOrder.SoldToParty` or `PurchaseDelivery.Supplier` | the customer or the supplier |

## 5. Reads

All examples use the root path from section 1. `{root}` stands for it. The responses are real and are
checked by a test against the data of 2026-10-31.

## 6. Notes for the SAP consultant

These are the usual SAP sources; confirm them and expose each entity as a read-only CDS view entity
with a projection, in the same service binding.

| Entity | Usual source |
|--------|--------------|
| `CashPayment` | cleared items of the customer, vendor and G/L accounts (`BSAD` for customers, `BSAK` for vendors, `BSAS` for the cost accounts) with the bank posting of the clearing document (`BKPF`, `BSEG`), or the bank statement lines |
| `CashSummaryBy*`, `ExpenseSummaryByDay` | aggregate CDS views over the `CashPayment` view, so SAP does the totalling |

The data is read with the shared management login, so the app limits who can ask for it (role
`management` or `admin`). Large tables must be selective on the filter fields used above:
`PostingDate`, `Direction`, `ExpenseCategory`, `CompanyCode`.
