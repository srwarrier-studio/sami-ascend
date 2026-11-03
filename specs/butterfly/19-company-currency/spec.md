# butterfly/19 company-currency

## Goal
Sales, purchase and receivable figures carry the amount in the company code currency (rupees) next to the amount in the document currency, so a consumer can show the whole business in one currency without converting anything itself.

## Why
About four in five sales orders are in dollars (every export). The apps now show rupees by default, and the sales, purchase and receivable summaries are in the document currency, so a rupee view leaves almost all export business out. SAP keeps the value of a document in the company code currency as well and does the conversion at the rate of the document, so the conversion belongs in the services (and later in SAP), not in synapse-api.

## Behavior
- **Convention.** A new pair of fields on each entity below: `...Local` (the amount in the company code currency) and `LocalCurrency` (`INR`). The existing amount and `Currency` fields do not change. Local is the document amount converted at the rate butterfly already uses (a dollar document is 80 rupees; a rupee document is itself), stored per document when the document is written and summed by the summaries.
- **Entities that get the pair** (fields appended at the end, so no existing field moves):
  - `SalesOrder`: `TotalNetAmountLocal`, `LocalCurrency` (read-only, computed by the service; a create request must not send them, like other service-filled fields).
  - `PurchaseDelivery`: `NetAmountLocal`, `LocalCurrency`.
  - `SalesSummaryByDay`, `SalesSummaryByCustomer`, `SalesSummaryByMaterial`: `TotalNetAmountLocal`, `LocalCurrency`.
  - `PurchaseSummaryByDay`, `...BySupplier`, `...ByMaterial`, `...ByMaterialGroup`: `TotalNetAmountLocal`, `LocalCurrency`.
  - `ReceivablesSummary` and `ReceivablesByCustomer`: `OpenAmountLocal`, `OverdueAmountLocal`, `LocalCurrency`; `ReceivablesAgeing`: `OpenAmountLocal`, `LocalCurrency`.
  The summaries still group by document `Currency`, so a consumer that wants one currency sums the `...Local` fields over all rows.
- **Stores.** New columns on the SQLite tables, written with each order, item, purchase item and invoice; the views and the receivables queries sum them; the in-memory repositories compute the same values; `$filter` and `$orderby` work on the new fields. An older database is rebuilt (layout version).
- **Contracts.** `sales-contract.md` and `drivers-contract.md` get the fields in their tables and the examples are regenerated from the real responses. `inventory`, `production` and `export` contracts are unchanged (already in the company currency).
- **synapse-api** (next phase) reads the local fields.

## Acceptance cases
- For every sales summary row group, `TotalNetAmountLocal` equals the sum over its orders of `TotalNetAmount` times the rate of the order currency (80 for USD, 1 for INR); the same for purchases and for open and overdue receivables as of any day.
- Over all rows, the sum of `TotalNetAmountLocal` of `SalesSummaryByDay` equals the sum of `TotalNetAmountLocal` of the orders it summarises, and a rupee-only row equals its document amount.
- An order created through the API shows the pair, with `TotalNetAmountLocal` = total x rate; `PATCH` keeps it.
- The database and the in-memory repositories answer the same for filters and ordering on the new fields.
- The contract tables, examples and field-table tests match the real responses; every existing test passes with its expectations updated only for the added fields.

## Out of scope
Exchange rate tables or rates by date (butterfly keeps its fixed rate; the real rate comes from SAP), other currencies than INR and USD, the synapse-api change, converting the document currency fields.

## Depends on
butterfly 18 (branch base).
