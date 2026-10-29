# synapse-web/02 widget-catalog

## Goal
The predefined sales widgets exist as a catalog on the `@sami/ui` registry, fed by mock sales data behind an interface, and a Widgets page shows all of them.

## Behavior
- `SalesData` is an interface shaped after the synapse-api routes: `today`, `monthToDate`, `yearToDate` (each `{ netAmount, previousNetAmount, orderCount, trend }`), `monthOnMonth(months)`, `daySales()` (this month and last month by day), `topCustomers(top)`, `topMaterials(top)`, `highValueOrders(top)`, `statusSplit()`. `MockSalesData` returns fixed numbers for a given date. Amounts are rupees (INR) as numbers.
- A catalog entry has `id`, `title`, `description`, `widget` (registry name) and `load(data)` returning that widget's props, each with a `measure` and a title. Entries: Sales today, Sales this month, Sales this year, Orders this month (KPI cards); Month-on-month sales (bar); Day sales (line with last month as compare); Recent high-value sales (table); Top customers and Top materials (ranked lists); Invoice status split (donut).
- `CatalogWidget` loads the props, shows a skeleton while loading, an error alert if loading fails, then the registry widget. Bad props fall back to the registry's fallback card.
- `/widgets` page ("Widgets", nav item) shows every entry in a grid.

## Acceptance cases
- Every entry's `load` on `MockSalesData` returns props the registry accepts (no fallback card).
- Entries have unique ids and a measure; KPI deltas come from the previous period; Day sales has a compare series.
- `CatalogWidget` shows a skeleton, then the widget; on failure the error message.
- The Widgets page lists every catalog title. Signed out goes to login.

## Out of scope
Boards, drag, refresh every 5 minutes (03), real API.

## Depends on
synapse-web 01, shared 09.
