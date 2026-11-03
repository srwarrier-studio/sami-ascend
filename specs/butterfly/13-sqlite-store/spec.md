# butterfly/13 sqlite-store

## Goal
Butterfly keeps its data in SQLite tables and answers the OData reads with SQL, so it behaves like a system with a database (persisting writes, summaries computed by the store) and every later domain (inventory, shipments, production output, payments) is added as tables, without changing a single OData shape.

## Why
Today all data is Python lists built at start-up. Summaries are recomputed in Python on every request, orders written through workspace-api vanish on restart, and each new domain would be more in-memory structures. SQLite behind the existing repository interfaces is the swap the architecture was built for, and the summary views become the specification the ABAP team builds CDS views from.

## Principles
- **The contract does not move.** Routes, entity sets, fields, query options, codes and error shapes in `docs/sap/` are unchanged. The existing butterfly tests (947) are the proof: they run against the SQLite store and pass without edits to their expectations.
- **SQLite is the store, not the SAP.** No SQLite-specific behaviour leaks into answers; the OData layer decides what a request means.
- **Interfaces stay.** `SalesOrderRepo`, `MasterDataRepo` and `DriverRepo` keep their methods; SQLite implementations sit beside the in-memory ones, which stay as test doubles. A new `QueryRepo` style read (below) is added only where push-down needs it.
- **No SQL from text.** Every column and sort name comes from the existing `*_FIELDS` whitelists; every value is a bound parameter.

## Behavior
- **Storage.** One database file, `BUTTERFLY_DB` (default `butterfly.db` in the working directory, ignored by git; `:memory:` allowed). Tables follow the entities: `customer`, `material`, `company`, `sales_order`, `sales_order_item`, `sales_contract`, `purchase_delivery`, `customer_invoice`, `production_order`, `production_order_component`. Amounts are stored as integers in minor units (cents, thousandths for quantities) so sums are exact; dates as ISO text; the repositories convert to and from `Decimal` and `date`.
- **Seeding.** The existing seeds (`small`, `story` with its scenarios) are written into the tables at start-up when the database is empty or its recorded `seed`, `scenario` or build day differ. The seeds are built relative to today, so a new day moves the seeded data (the demo dashboards depend on it); orders written through the API (`origin = 'api'`) are kept across that rebuild, and the number sequence continues after them. A restart with the same settings on the same day keeps everything.
- **Writes.** `POST SalesOrder` and `PATCH SalesOrder` persist; a restart returns them; the number sequence continues from the highest stored number; the `ETag` still comes from `LastChangeDateTime`.
- **Reads.** `SalesOrder`, `SalesOrder('key')`, `_Item` and the driver entities answer through SQL: `$filter` becomes a parameterised `WHERE`, `$orderby` an `ORDER BY` (with a stable tie-break on the key), `$top`/`$skip` a `LIMIT`/`OFFSET`, `$count` a `COUNT`, `$select` the column list, `$expand=_Item` a second query. A filter the parser accepts today is accepted and means the same; one it refuses today is refused with the same message.
- **Summaries as views.** `SalesSummaryByDay`, `...ByCustomer`, `...ByMaterial` and the three purchase summaries are SQL views over the tables (cancelled `X` left out as today). The three receivables entities take `AsOfDate`, so they are queries with a bound date, not static views. The view and query text live in `docs/sap/views/` as the plain statements the ABAP team can turn into CDS views, and the tests read the same files.
- **Concurrency.** One connection shared by the requests behind a lock (`check_same_thread=False`), `PRAGMA foreign_keys=ON`, WAL mode for a file; a failed write leaves nothing half-written (one transaction per write). Reads are serialised; that is enough for a stand-in (per-thread connections if it ever is not).
- **Nothing for the apps to change.** synapse-api, workspace-api and the web read the same URLs.

## Acceptance cases
- With `BUTTERFLY_DB=:memory:` and each seed, every existing butterfly test passes unchanged, including `test_story_ground_truth` and the scenario ground-truth tests.
- Create an order, restart butterfly with the same file: the order is returned and the next number follows it.
- Start with a different `BUTTERFLY_SEED` or `BUTTERFLY_SCENARIO` on an existing file: the data is rebuilt to the new seed.
- A `$filter` with a quote, `--` or `;` in a value returns the right rows and never executes the text.
- `SalesSummaryByDay` with `$filter` on `CompanyCode` equals the totals computed from `SalesOrder` rows by hand.
- A request for 1,000 rows of `SalesOrder` on the story seed is not slower than today.
- Opening the view files in `docs/sap/views/` shows one statement per summary entity.

## Out of scope
New entities and domains (inventory, shipments, production output, payments, material groups: butterfly 14 to 18), moving workspace-api's own database, schema migrations (a rebuild from seed is the migration while butterfly is a stand-in), Postgres, authentication.

## Depends on
butterfly 12 (merged). No app changes.

## Decisions (owner, 2026-11-03)
1. The database is a file (`BUTTERFLY_DB`, default `butterfly.db`), so data survives restarts; `:memory:` stays available for tests.
2. Money and quantities are stored as integers in minor units (cents, thousandths).
