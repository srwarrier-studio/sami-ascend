# butterfly/03 sales-summaries

## Goal
Butterfly serves the three read-only summary entities of `docs/sap/sales-contract.md` section 2, computed from the orders in the repo, so a created order shows in the totals at once.

## Behavior
- **Entities:** `SalesSummaryByDay`, `SalesSummaryByCustomer`, `SalesSummaryByMaterial`, fields and keys as in the contract. `GET {root}<Entity>` returns `{"@odata.context": "$metadata#<Entity>", "value": [...]}`. Reading one row by key is not supported (`404 RESOURCE_NOT_FOUND`); callers use `$filter`.
- **Computed on every request** from `SalesOrderRepo`, nothing stored. Orders created or changed through butterfly appear in the next read.
- **Grouping:** by `OrderDate` (day), by `SoldToParty` + `OrderDate`, by `Material` + `OrderDate` (from items), one row per key and currency. `OrderCount` counts orders (for material: not provided, per the contract). `TotalNetAmount` sums order `TotalNetAmount` (day, customer) or item `NetAmount` (material). `TotalQuantity` sums item `Quantity`; the unit is the material's single unit.
- **Cancelled orders** (`OverallStatus` `X`) are left out of every summary. Questions for consultants: does a real summary view exclude them? (add to `consultant-questions.md`).
- **Days without orders** have no row.
- **Query options:** `$filter`, `$select`, `$orderby`, `$top`, `$skip`, `$count` through the existing `apply_list_query`, with a field table per summary. Default order when no `$orderby`: `OrderDate` ascending, then the other key fields. `$expand` returns `UNSUPPORTED_QUERY_OPTION` (already in the contract).
- **Money:** decimals as strings with the contract scale (`15,2` amounts, `13,3` quantities), summed exactly with `Decimal`.

## Acceptance cases
- The seed gives one day row per seed date; each equals the sum of that day's non-cancelled orders; the day rows' `OrderCount` add up to the non-cancelled order count.
- Customer and material rows each add up to the day totals for the same date.
- POST an order for today: the day, customer and material rows for today change by exactly its amounts; `OrderCount` goes up by one.
- Cancel-status seed orders do not count; a PATCH never changes totals.
- `$filter=OrderDate ge ... and OrderDate le ...&$orderby=OrderDate` returns the contract's summary example shape; `$select`, `$top`, `$skip`, `$count=true` work as on `SalesOrder`.
- `$expand` and an unknown field in `$filter` give `400` in the error format.
- `test_contract.py` checks the three field tables and runs the summary example (no longer skipped).

## Out of scope
Month-to-date and year-to-date (synapse-api sums days), multiple currencies in seed data (butterfly only has `INR`, grouping still keys on currency), `$apply`, caching, delays and failures (butterfly/04), `$metadata`.

## Depends on
butterfly/01 and 02 (done).
