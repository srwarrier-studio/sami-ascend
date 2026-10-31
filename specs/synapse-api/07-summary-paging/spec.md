# synapse-api/07 summary-paging

## Goal
synapse-api reads every sales summary completely, however many days it covers, so dashboards and answers never show zero or partial months.

## Behavior
- `ButterflySalesSource` reads `SalesSummaryByDay`, `SalesSummaryByCustomer` and `SalesSummaryByMaterial` in pages of `PAGE` (1000) rows with `$top` and `$skip`, and keeps reading until a page has fewer than `PAGE` rows, then returns all rows. A result of exactly `PAGE` rows takes one more request, which comes back empty.
- Pages must not overlap or skip rows, so each summary is ordered by its whole key: day by `OrderDate,Currency`; customer by `OrderDate,SoldToParty,Currency`; material by `OrderDate,Material,Currency`.
- `order_statuses` already pages; it shares the same helper and sends exactly the same requests as before.
- An error on any page (status other than 200, connection error, unreadable body) is `SapUnavailable` for the whole call; a partial result is never returned.
- Nothing else changes: the rows, the mapping and the 5-minute cache are as before.

## Why
Found by running butterfly's 14-month story seed through synapse-api: the month-on-month sales showed the first 100 days correctly and 0 for every month after. Butterfly caps a response at 100 rows by default and the real SAP service caps page size too; the old seed had only 10 days, so it never showed.

## Acceptance cases
- Each of the three summaries asks for `$top=1000&$skip=0` first, ordered by its key.
- Two pages (1000 rows, then 3) give 1003 rows and two requests with `$skip` 0 and 1000.
- Exactly 1000 rows give 1000 rows and a second, empty request.
- A short first page gives one request.
- A failure, bad status or unreadable body on the second page raises `SapUnavailable` and returns nothing.
- `order_statuses` sends the same requests as before.
- The request id is sent on every page.

## Out of scope
Server-driven paging with `@odata.nextLink` (butterfly and the contract use `$top` and `$skip`), larger pages, reading pages in parallel.

## Depends on
synapse-api 01, butterfly 08 (which exposed it).
