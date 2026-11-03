# synapse-api/14 production-widgets

## Goal
The seven Production widgets of the catalog read butterfly (the production service of butterfly 16 and the production orders of the drivers service) instead of `mock_library.json`, and a board with production widgets gets a production topic in its overview.

## Why
Production is the next domain still on fixed numbers. Butterfly 16 serves the shop floor as SAP will; this phase reads it through a gateway so the real system replaces butterfly later without a change here.

## Behavior
- **Gateway.** `ProductionSource` with a butterfly implementation reading `ProductionSummaryByDay`, `DowntimeSummaryByDay`, `ScrapSummaryByDay`, `OutputSummaryByLineShift` (production service) and `ProductionOrder` with status `R` (drivers service), scoped by company, and a mock for tests. New setting `PRODUCTION_BASE_URL`.
- **Windows.** The shop floor follows the orders' calendar (butterfly runs a batch a month), so a calendar day or month to date is often empty. Widgets use trailing windows ending today: 30 days for output, effectiveness and the line heat map, 90 days for downtime and scrap, six calendar months for output against plan.
- **Widgets, same ids so saved boards keep working** (value in rupees at standard price, default INR; other currencies left out):
  - `prod-output` KPI, titled `Output, last 30 days`: good output value over the last 30 days against the 30 days before, with the last six 30-day windows as the trend; caption `last 30 days vs the 30 before`.
  - `prod-oee` gauge: equipment effectiveness over the last 30 days = availability x performance x quality, where availability = 1 - downtime hours / planned hours, performance = (good + scrap value) / target value, quality = good / (good + scrap value); target 85%; caption `last 30 days`, or `no production in 30 days` with a value of 0.
  - `prod-plan` line chart: good output per month for six months against the plan (target value), labelled `Output` and `Plan`.
  - `prod-downtime` bar chart: downtime hours by cause over 90 days, most first, causes named `Breakdown`, `Changeover`, `No material`, `Maintenance`, `Other`.
  - `prod-scrap` donut: scrap value by reason over 90 days, named `Material defect`, `Machine setting`, `Operator error`, `Other`.
  - `prod-heat` heat map: good output by line and shift over 30 days (rows `Line 1` to `Line 3` summed over plants, columns `Morning`, `Afternoon`, `Night`).
  - `prod-orders` table: released orders not yet complete, earliest start first, top 5; columns order, item, status (`Planned` before its start, `In progress` from its start, `Late` after its planned end) and planned quantity.
- **Status colour (`@sami/ui`).** `Late` is drawn as needing attention; `Planned` and `In progress` stay neutral.
- **Overview.** A production topic when the board has a production widget, at most two sentences, after Inventory:
  1. Headline (always): `Output over the last 30 days was <amount>, up|down X% on the 30 days before.` (no comparison when the 30 days before had none; nothing when both are zero).
  2. With `prod-oee`: `Equipment effectiveness is X% over the last 30 days, held back most by <availability|performance|quality>.`
  3. With `prod-downtime`: `<Cause> caused the most downtime in the last 90 days: <n> hours.`
  4. With `prod-scrap`: `<Reason> caused the most scrap in the last 90 days: <amount> (<share>% of scrapped output).`
- Nothing already served changes shape; the mock library no longer lists or serves a `prod-*` id.

## Acceptance cases
- `prod-output` value, delta and six trend windows from daily rows; no delta when the previous window is empty.
- `prod-oee` equals availability x performance x quality worked out by hand from the same rows; no rows gives 0 with the caption.
- `prod-plan` has six months ending this one with output and plan; `prod-downtime` and `prod-scrap` are sorted biggest first and leave out other currencies and older rows; `prod-heat` has a cell per line and shift with output.
- `prod-orders` lists only unfinished orders, earliest start first, with the right status word.
- The overview: sales then production sentences for a board with `sales-month` and `prod-oee`; the weakest factor is named.
- With butterfly 16 running, the widgets match direct reads; the catalog has no duplicate ids and `exp-*` and `fin-collections` are still served by the mock library.

## Out of scope
Exports and Finance cash widgets, a real OEE target from the business, line-level (machine) detail, any butterfly change.

## Depends on
butterfly 16 (production service), synapse-api 12 and 13 (branch base: sources and catalog composition).
