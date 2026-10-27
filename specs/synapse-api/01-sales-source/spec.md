# synapse-api/01 sales-source

## Goal
synapse-api can read sales data through a `SalesSource` interface, with a mock implementation for tests and an implementation that calls butterfly over OData V4.

## Behavior
- **Domain:** `DailySales` (date, net amount, order count, currency), `CustomerSales` (customer, name, date, net amount, order count, currency), `MaterialSales` (material, description, date, quantity, unit, net amount, currency), `HighValueOrder` (order, customer name, order date, net amount, currency, status). Plain frozen dataclasses, decimals as `Decimal`, dates as `date`. Error `SapUnavailable`.
- **Interface `SalesSource`:** `daily_sales(start, end)`, `customer_sales(start, end)`, `material_sales(start, end)` (rows per day per currency, dates inclusive, ordered by date), and `high_value_orders(minimum, top)` (cancelled excluded, newest first). Adding up days, ranking and caching are phase 02.
- **Mock:** `MockSalesSource` holds the rows it is given, filters by date, and can be told to fail with `SapUnavailable`.
- **Butterfly source:** `GET SalesSummaryByDay|ByCustomer|ByMaterial?$filter=OrderDate ge <start> and OrderDate le <end>&$orderby=OrderDate`; `GET SalesOrder?$filter=TotalNetAmount ge <minimum> and OverallStatus ne 'X'&$orderby=CreationDateTime desc&$top=<top>`. Base URL from `Settings` (`SAP_BASE_URL`, default the butterfly root). Sends `X-Request-ID` from `get_request_id()`. Query strings built by hand with `%20`, as in workspace-api.
- **Errors:** connection error, timeout, `5xx`, any status other than `200`, or an unreadable body becomes `SapUnavailable`.
- **Logging:** `setup_logging("synapse-api")` when the package entrypoint is imported. No sales figures in logs.
- **Layout:** `domain`, `application`, `infrastructure`, `entrypoint`. No use cases and no routes here (phases 02-03); the interface is the deliverable.
- **Dependencies:** `httpx`, `structured-logging` (workspace package), `fastapi[standard]` is not needed yet.

## Acceptance cases
- Mock: rows outside the date range are dropped; the range is inclusive; failure mode raises `SapUnavailable`.
- Butterfly source (tests use `httpx.MockTransport`, never the network): each method builds the expected query; each maps the contract example rows; decimals stay exact (`"845000.00"` becomes `Decimal("845000.00")`); an empty `value` gives an empty list.
- `503`, `404`, timeout, connection error and a body without `value` map to `SapUnavailable`.
- `X-Request-ID` is sent when a request id exists and omitted otherwise.

## Out of scope
Use cases, KPIs, caching, the 5-minute refresh, routes, authentication and roles, `$count`, paging through more than `$top` rows, retries, running against real butterfly (shared/05), `401`/`403` mapping (shared/04).

## Depends on
butterfly 01 and 03 (done), shared 03 structured-logging (done).
