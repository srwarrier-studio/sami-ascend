# synapse-api/12 inventory-widgets

## Goal
The nine Inventory widgets of the catalog read their numbers from butterfly's inventory service (`docs/sap/inventory-contract.md`) instead of `mock_library.json`, and a board with inventory widgets gets an inventory sentence in its overview.

## Why
Phase 11 moved the Purchase and Receivables widgets to butterfly; stock is the largest group still on fixed numbers. Butterfly 14 serves stock as the SAP service will, so synapse-api reads it through a gateway and the real system replaces butterfly later without a change here.

## Behavior
- **Gateway.** `InventorySource` (domain) with a butterfly implementation reading `MaterialStock`, `StockSummaryByStatus`, `...ByWarehouse`, `...ByMaterialGroup`, `StockValueByMonth`, `StockMovementSummaryByDay` and `...ByHour` through the existing `ODataReader`, scoped by company like the other sources, and a mock implementation for tests. New setting `INVENTORY_BASE_URL` (default butterfly's inventory root).
- **Widgets, same ids so saved boards keep working** (amounts in the requested currency, default INR; rows in another currency are left out):
  - `inv-value` KPI: stock value now (sum of the warehouse summary) against the value at the end of last month (`StockValueByMonth`), with the month-end trend of six months; caption `vs <last day of last month>`.
  - `inv-low` KPI: items below their reorder level (status `L` and `Z`), caption `<n> out of stock`; no delta (there is no history of it).
  - `inv-availability` gauge: share of stock rows that are not at zero, against 100%.
  - `inv-warehouses` bar chart: stock value per storage location, labelled with its name and, when more than one plant is read, the plant.
  - `inv-groups` donut: stock value per material group (groups with no value left out; more than six are grouped as Other by the donut).
  - `inv-slow` ranked list: the in-stock items whose last movement is oldest, value = days since the last movement, top 5.
  - `inv-movement` line chart: receipts against issues per day for the last 14 days, in value; missing days are zero.
  - `inv-reorder` table: items below their reorder level, out of stock first, then by how far below (stock over level), top 5, with columns material, in stock, reorder at, status (`Out of stock` or `Low`).
  - `inv-heat` heat map: goods movements by weekday and hour over the last 90 days (rows Mon to Sun that have movements, columns `8am` to `5pm`).
- **Status colour (`@sami/ui`).** `Out of stock` is drawn as needing attention (red) and `Low` as caution; they are in the word lists of `status.ts`.
- **Overview.** The board summary gets an Inventory topic written when the board has an inventory widget, at most two sentences, in the order Sales, Purchases, Receivables, Inventory:
  1. Headline (always): `Stock is worth <amount>, up|down X% on the end of <month>.` (no comparison sentence part when there was no value at last month end).
  2. With `inv-low` or `inv-reorder`: `<n> items are below their reorder level, <m> of them out of stock.` (left out when none).
  3. With `inv-groups`: `<group> holds the most stock: <amount> (<share>% of its value).`
  4. With `inv-slow`: `<item> has not moved for <n> days.`
  The first two that apply are returned.
- Nothing already served changes shape. The mock library no longer lists or serves an `inv-*` id.

## Acceptance cases
- With stock rows, `inv-value` has the value, the delta against the last month-end value, six trend points and the caption date; with no month-end history it has no delta.
- `inv-low` counts `L` and `Z` rows and says how many are out of stock; `inv-availability` is rows with stock over all rows.
- `inv-warehouses` has one bar per location and adds the plant to the label only when several plants are present.
- `inv-slow` excludes zero stock and orders by the oldest last movement; `inv-reorder` puts out of stock first.
- `inv-movement` has 14 points, zeros for days without movements; `inv-heat` has only weekday and hour combinations with movements.
- The catalog list has no duplicate id, `inv-*` come from the real source, and `fin-collections` is still served by the mock library.
- A board with `inv-value`, `inv-low` and `sales-month` gets sales then inventory sentences; a board with only `inv-groups` gets the headline and the group sentence.
- With butterfly (inventory) running, every widget returns numbers that match a direct butterfly read.

## Out of scope
Butterfly changes, forecasting reorder quantities, stock by batch or by plant on request, the other mock domains (Exports, Production, Finance cash, Purchase categories).

## Depends on
butterfly 14 (inventory service), synapse-api 11 (sources and catalog composition), synapse-web 18 (board summary).
