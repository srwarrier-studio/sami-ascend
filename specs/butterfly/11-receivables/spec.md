# butterfly/11 receivables

## Goal
Butterfly serves customer invoices with due dates and payments, and receivable summaries, so synapse-api can show what customers owe without any mock data.

## Behavior
### Contract (`docs/sap/drivers-contract.md`, changed first)
- New read-only entity `CustomerInvoice` in the drivers service: `Invoice` (key), `SoldToParty`, `CustomerName`, `InvoiceDate`, `DueDate`, `NetAmount` (`Edm.Decimal` 15,2), `TransactionCurrency` (`INR`), `ClearedAmount` (`Edm.Decimal` 15,2), `ClearingDate` (`Edm.Date`, empty while nothing is cleared). Same query options and paging as the other entities.
- Three read-only summary entities, all measured on an as-of date given as the custom query parameter `AsOfDate` (default: butterfly's today); an invoice counts when `InvoiceDate <= AsOfDate`, and its open amount is `NetAmount - ClearedAmount` counting only clearings on or before `AsOfDate`:
  - `ReceivablesSummary` (`AsOfDate`, `OpenAmount`, `OverdueAmount`, `OpenCount`, `OverdueCount`, `Currency`);
  - `ReceivablesByCustomer` (adds `SoldToParty`, `CustomerName`), customers with nothing open are left out;
  - `ReceivablesAgeing` (`AsOfDate`, `AgeBucket`, `OpenAmount`, `OpenCount`, `Currency`), buckets `current` (not yet due), `1-30`, `31-60`, `61-90`, `90+` days past due.
- Overdue means `DueDate < AsOfDate` and still open.

### Data
- One invoice per sales order, derived with fixed arithmetic: invoice date is the order date, net amount is the order's net amount, due date is the invoice date plus the customer's payment terms (30, 45 or 60 days, fixed per customer).
- Each customer has a fixed payment delay in days (0 to 75) added to the due date; an invoice is cleared in full on that date when it falls on or before today, otherwise it stays open. A few customers are slow payers so ageing has every bucket and some customers owe much more than others. No random numbers.
- Cancelled sales orders and items produce no invoice. Existing scenarios keep their sales, driver and purchase data unchanged (pinned by hashes); invoices follow from each scenario's sales.

## Acceptance cases
- Contract tests: the field table and examples in the drivers contract for `CustomerInvoice` and the three summaries match butterfly.
- Each invoice equals its sales order (customer, date, amount); cancelled orders have none; due date follows the customer's terms; the clearing date follows the delay; cleared amount is the full amount or zero.
- `ReceivablesSummary` open amount equals the sum of the open amounts of the invoices; overdue is the part with `DueDate < AsOfDate`; `ReceivablesByCustomer` adds up to the summary and is ordered by customer; `ReceivablesAgeing` buckets add up to the open amount, each invoice sits in one bucket, and every bucket has data in the default scenario.
- An earlier `AsOfDate` ignores later invoices and later clearings.
- Paging, `$count` and `$filter` work like the sales summaries.
- Data hashes of every earlier list stay unchanged.

## Out of scope
Payments recorded as separate documents, partial payments, credit notes, other currencies and exchange rates, dunning, writes, why-analysis scenarios for receivables, synapse-api reads (the next phase).

## Depends on
butterfly 10, `docs/sap/drivers-contract.md`.

## Open questions for the owner
- Is one invoice per sales order acceptable, or should invoices be built from the order items?
- Payment terms and delays are invented; should any real SAP terms (e.g. `ZTERM` codes) be mirrored in the contract?
