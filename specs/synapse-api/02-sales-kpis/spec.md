# synapse-api/02 sales-kpis

## Goal
synapse-api turns `SalesSource` rows into the sales numbers the dashboard needs, cached and refreshed every 5 minutes.

## Behavior
- **Domain:** `SalesTotal` (period start, period end, net amount, order count, currency), `RankedCustomer` (customer, name, net amount, order count, currency), `RankedMaterial` (material, description, quantity, unit, net amount, currency), `MonthSales` (year, month, net amount, currency). Frozen dataclasses, `Decimal` amounts.
- **Use cases** (one class, one `execute`, each takes a `SalesSource` and `today: date`):
  - `GetTodaySales`: one `SalesTotal` per currency for `today`.
  - `GetMonthToDateSales`: first of the month to `today`, summed per currency.
  - `GetYearToDateSales`: 1 January to `today`, summed per currency.
  - `GetMonthOnMonthSales(months)`: last `months` calendar months including the current one, one `MonthSales` per month per currency, oldest first, missing months as zero. Default 12.
  - `GetTopCustomers(top)` and `GetTopMaterials(top)`: month to date, summed over days, ranked by net amount descending, per currency. Default 5.
  - `GetRecentHighValueOrders(minimum, top)`: passes through `high_value_orders`.
- **Currencies are never added together.** Every result is per currency.
- **Cache `SalesCache`:** holds the results of the use cases above under a key, with a time-to-live of 5 minutes (`Settings.CACHE_SECONDS`, default 300) and an injectable clock. A read inside the time-to-live returns the stored value. A read after it calls the use case again. If SAP fails on refresh and a stored value exists, the old value is returned and the failure is logged; with nothing stored, `SapUnavailable` propagates.
- **Refresh style:** on read, not a background loop. Simplest, and a widget that nobody opens costs no SAP calls.
- **Input rules:** `top` outside 1..50 and `months` outside 1..24 raise `InvalidQuery` (domain error). Routes (phase 03) turn it into 422.
- **Layout:** `domain`, `application` (use cases, `SalesCache`), no routes, no new dependencies.

## Acceptance cases
- Today, MTD and YTD: a mock with rows on several days and two currencies gives one total per currency; rows outside the period are not counted; the first and last day of the period are included.
- MoM: a month with no rows is returned as zero; the year boundary (January looks back to December) is right; order is oldest first.
- Top customers and materials: summed over days, ranked descending, cut to `top`; ties keep a stable order (by id); currencies ranked separately.
- High-value orders: passes `minimum` and `top` through.
- Invalid `top` or `months` raises `InvalidQuery` and does not call the source.
- Cache: second read inside 5 minutes does not call the source; read after 5 minutes does; a failed refresh returns the old value; a failed first read raises; different keys do not share values.

## Out of scope
Routes, roles, board storage, a background scheduler, per-user data, comparisons against targets or last year, currency conversion, persistent cache, running against real butterfly (shared/05).

## Depends on
synapse-api 01 (done).
