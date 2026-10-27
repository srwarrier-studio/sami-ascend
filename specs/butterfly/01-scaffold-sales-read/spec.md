# butterfly/01 scaffold-sales-read

## Goal
A new app, butterfly, that serves `SalesOrder` reads from seed data with the OData V4 query options and error format in `docs/sap/sales-contract.md`, so gateways can be built before SAP exists.

## Behavior
- New uv workspace member `apps/butterfly` (FastAPI), port 8003, layers as in the constitution (`domain`, `application`, `infrastructure`, `entrypoint`). Uses `structured-logging`; no auth yet (identity is shared/04).
- Served under the contract root `/sap/opu/odata4/sap/zui_sales_o4/srvd_a2x/sap/zsales/0001/`.
- Routes: `SalesOrder` (collection), `SalesOrder('key')` (with `@odata.etag`), `SalesOrder('key')/_Item`, and `$expand=_Item` on the collection and the single order.
- Seed data is built in code by a function taking `today`: about 30 orders over the last 10 days, 2 to 3 items each, 5 customers, 6 materials, all four statuses, INR only. Same `today` gives the same data. The data sits behind a `SalesOrderRepo` interface so butterfly/02 can add writes.
- Query options exactly as contract section 4: `$filter` (`eq ne gt ge lt le`, `and or not`, `contains()`, `startswith()`, parentheses; string, date and decimal literals), `$select`, `$orderby`, `$top` (default 100, over 1000 is 400), `$skip`, `$count=true`, `$expand=_Item`. Parsed with a small hand-written parser, no new dependency.
- Responses follow contract section 5: decimals as strings, `Edm.Date`, UTC timestamps with `Z`, `@odata.context`, `@odata.count` only when asked, no `@odata.nextLink`.
- Errors follow contract section 7: unsupported option `UNSUPPORTED_QUERY_OPTION` (400), unknown order `SALES_ORDER_NOT_FOUND` (404), bad `$filter` or unknown field `INVALID_QUERY` (400), unexpected error `INTERNAL_ERROR` (500) with the request id as `target`.

## Acceptance cases
- Each contract section 5 read example gives the same shape with seed values (checked against the field tables in a test).
- Every operator, function and `and/or/not` combination in section 4 filters correctly; precedence is `not` over `and` over `or`; parentheses work.
- `$select` limits fields; `$orderby` with several keys and `desc`; `$top`, `$skip`, `$count` agree with the filter (count ignores `$top`/`$skip`).
- `$top=1001`, `$apply`, `$search`, `$expand=Other`, lambda operators, an unknown field and a malformed filter each return the right 400 with `code` and `target`.
- Unknown order key is 404 in the error format. A raised exception is 500 with no stack trace in the body.
- Same query on the same seed always returns the same rows in the same order.
- The `.venv` runs `butterfly` with no network and no SAP.

## Out of scope
Writes (butterfly/02), summary entities (butterfly/03), delays and failures (butterfly/04), `$metadata`, top-level `SalesOrderItem` set, authentication, persistence across restarts, `@odata.nextLink`.

## Depends on
shared/01 (contract), shared/03 (logging). Both done.
