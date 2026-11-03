# synapse-api/15 export-widgets

## Goal
The seven Exports widgets of the catalog read butterfly's export service (`docs/sap/export-contract.md`) instead of `mock_library.json`, and a board with export widgets gets an exports topic in its overview.

## Why
Exports is one of the two domains left on fixed numbers (with Finance cash). Butterfly 17 serves shipments as SAP will; this phase reads them through a gateway so the real system replaces butterfly later without a change here.

## Behavior
- **Gateway.** `ExportSource` with a butterfly implementation reading `ExportSummaryByDay`, `ExportSummaryByDestination`, `ExportSummaryByMode` and `ExportShipment` (status `T`), scoped by company, and a mock for tests. New setting `EXPORT_BASE_URL`.
- **Widgets, same ids so saved boards keep working** (value in rupees, the company currency of the contract; default INR):
  - `exp-shipments` KPI: shipments so far this month against the same days last month, with the day ranges, partial note and six-month trend like the sales KPIs.
  - `exp-revenue` KPI: export value so far this month against the same days last month, same shape.
  - `exp-trend` area chart: export value for each of the last six months.
  - `exp-destinations` ranked list: destination countries by value over the last 90 days, top 5.
  - `exp-modes` donut: shipments by mode (Sea, Air, Road) over the last 90 days.
  - `exp-transit` table: shipments in transit, earliest expected arrival first, top 5; columns shipment, destination, status (`In transit`, or `Late` when the expected arrival is before today) and value.
  - `exp-calendar` year calendar: shipments per day over the last 365 days.
- **Overview.** An exports topic when the board has an export widget, at most two sentences, after Production:
  1. Headline (always): `Exports this month are <n> shipments worth <amount> (<days>[, N of M days so far]), up|down X% on <days>.` (the sales wording; no comparison part when last month's days had none; nothing when both are zero).
  2. With `exp-transit`: `<n> shipments are in transit, <m> of them past their expected arrival.` (left out when none are in transit).
  3. With `exp-destinations`: `<Country> is the top destination over the last 90 days: <amount> (<share>% of exports).`
  4. With `exp-modes`: `<Mode> carries <share>% of shipments over the last 90 days.`
- `@sami/ui`: `In transit` is a neutral status word; `Late` is already drawn as needing attention.
- Nothing already served changes shape; the mock library no longer lists or serves an `exp-*` id.

## Acceptance cases
- `exp-shipments` and `exp-revenue` give value, delta, `period`, `comparedWith`, the partial note early in the month and a six-month trend, like `sales-month`.
- `exp-destinations` ranks by value and leaves out older rows; `exp-modes` names the modes and drops zero modes; `exp-trend` has six months ending this one.
- `exp-transit` lists only shipments in transit, earliest arrival first, with `Late` for those past their expected arrival.
- `exp-calendar` has one point per day with shipments within 365 days.
- The overview names the top destination and mode, counts late shipments, and respects the two-sentence cap per topic.
- With butterfly 17 running the widgets match direct reads; the catalog has no duplicate id and `fin-collections` is still served by the mock library.

## Out of scope
Finance cash widgets, freight cost, real exchange rates, any butterfly change.

## Depends on
butterfly 17 (export service), synapse-api 14 (branch base, catalog composition).
