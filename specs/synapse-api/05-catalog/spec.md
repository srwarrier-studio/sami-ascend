# synapse-api/05 catalog

## Goal
synapse-api serves the widget catalog and, for each entry, the ready-to-render widget props, so synapse-web holds only views.

## Behavior
- `GET /v1/synapse/catalog` returns `[{ id, title, description, category, widget }]`, roles `management` and `admin`. `widget` is a `@sami/ui` registry widget name.
- `GET /v1/synapse/catalog/{id}/data` returns the JSON props that widget renders with: exactly what synapse-web's `entry.load(data)` returns today (`title`, `measure`, `value`, `valueFormat`, `delta`, `caption`, `trend`, `slices`, `series`, `rows` and so on). Numbers are JSON numbers. An unknown id is 404 `CATALOG_ENTRY_NOT_FOUND` in the same error shape as the other routes.
- Domain: `CatalogEntry` entity (the five fields) and a `WidgetCatalog` port with `entries()` and `data(id)`. Use cases `ListCatalog` and `GetWidgetData`, one `execute` each.
- Sales entries (sales today, this month and year, orders this month, month-on-month, day sales, month target, status split, top customers, top materials, high-value orders) are built from `SalesSource` and the existing use cases. Day sales is built from the existing `daily_sales`; the month target is the `MONTHLY_SALES_TARGET` setting (default 5,000,000), since a target is not SAP data. `SalesSource` gains `order_statuses(start, end)` (one row per non-cancelled order with its date and status code); the mock keeps a list and butterfly reads `SalesOrder` with `$select` and pages with `$top` and `$skip`. The status split counts this month's orders by name (Open, In process, Completed); its title and category stay as the web catalog has them.
- The other entries the board offers today (Purchases, Inventory, Finance and the rest of `mockLibrary`) come from a `MockLibraryCatalog` with the same ids, titles, domains and props as `packages/ui/src/mockLibrary.ts`; a later phase replaces each with real SAP data. The playground keeps its own copy.
- Widget data goes through the existing 5-minute `SalesCache`, keyed by catalog id and today's date.
- The mapping from source data to props lives in `application/` (one small class per widget shape), not in the router.

## Acceptance cases
- Catalog list: contains every id the web catalog has today, with category and widget name; sorted as the web catalog is.
- Data: for every entry the props validate against the registry schema for its widget (a test reads `registry.describe()` output exported to a fixture, or checks the required keys per widget); sales entries equal what the web `load` returned for the same mock data.
- `order_statuses` on the mock and butterfly sources (query, mapping, paging), with tests; day sales, month target and status split entries.
- Routes: management and admin get 200; sales role 403; no token 401; unknown id 404; second call inside 5 minutes does not hit the source again.
- Existing sales routes are unchanged.

## Out of scope
Real SAP data for the library entries, parameterised widgets, boards, the web app changes (synapse-web 06), AI.

## Depends on
synapse-api 03.
