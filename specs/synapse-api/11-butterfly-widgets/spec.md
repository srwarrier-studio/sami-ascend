# synapse-api/11 butterfly-widgets

## Goal
The Purchase and Receivables widgets of the catalog read their numbers from butterfly (the stand-in for the SAP RAP services) instead of `mock_library.json`.

## Why
Butterfly is the one source of data and is replaced by the real SAP OData V4 services later without a code change in the apps. Today 39 of the 50 catalog widgets are fixed numbers in a JSON file inside synapse-api. Butterfly already serves purchases (`PurchaseSummaryByDay`, `PurchaseSummaryBySupplier`, `PurchaseDelivery`) and receivables (`ReceivablesSummary`, `ReceivablesByCustomer`, `ReceivablesAgeing`) in `docs/sap/drivers-contract.md`, so nothing new is needed from butterfly for these.

## Program (all of the mock library moves to butterfly)
| Domain | Widgets | Source | Phase |
|--------|---------|--------|-------|
| Purchase | spend, open orders, trend, top vendors, recent orders, on-time delivery | existing butterfly entities | this phase |
| Finance | receivables outstanding, ageing, most overdue | existing butterfly receivables entities | this phase |
| Purchase | spend by category, by category per month | needs a material group in the contract | butterfly 14 |
| Inventory | all 9 | new stock service (contract in `docs/sap/` first) | butterfly 13 |
| Exports | all 7 | new shipment entity and destination | butterfly 15 |
| Production | output, effectiveness, plan, downtime, scrap, heat, open orders | `ProductionOrder` exists; output, downtime and scrap are new | butterfly 16 |
| Finance | collections, target, cash in and out, payments, expenses | new payment and expense entities | butterfly 17 |
Each butterfly phase writes its contract in `docs/sap/` first (the document the ABAP team builds from), then serves it with the same OData V4 shapes, query options and naming as the existing services, then synapse-api reads it. Widgets that are not moved yet keep their mock values until their phase.

## Behavior
- New gateways `PurchaseSource` and `ReceivablesSource` (domain), with butterfly implementations that read through the existing `ODataReader` and mock implementations for tests. Both are scoped by company like `SalesSource`.
- Catalog ids that have a real source keep their ids (`pur-spend`, `pur-open`, `pur-trend`, `pur-vendors`, `pur-recent`, `pur-ontime`, `fin-receivables`, `fin-ageing`, `fin-overdue`), so saved boards keep working. The mock library no longer lists or serves an id a real catalog serves.
- Purchase widgets:
  - `pur-spend` KPI: purchases this month against the same days last month, with the day ranges, partial note and trend as the sales KPI.
  - `pur-open` KPI: number of open purchase order items (`DeliveryStatus eq 'O'`).
  - `pur-trend` area chart: purchases per month for 12 months.
  - `pur-vendors` ranked list: top 5 suppliers by spend this month.
  - `pur-recent` table: the latest purchase order items by order date.
  - `pur-ontime` gauge: of the items promised in the last 90 days up to today, the share delivered on or before the promised date (an item not delivered yet counts as late). The window is 90 days because butterfly, like SAP, places orders about the 24th of a month, so a calendar month is often empty.
- Receivables widgets, measured on today (`AsOfDate`): `fin-receivables` KPI (open amount, caption with the overdue amount), `fin-ageing` bar chart (one bar per bucket in the order `current`, `1-30`, `31-60`, `61-90`, `90+`), `fin-overdue` ranked list (top 5 customers by overdue amount).
- Money is in the requested currency (default INR); rows in other currencies are left out, as for sales. All sources read only through the OData query options in the contract.

## Acceptance cases
- With purchase rows for this month and the same days last month, `pur-spend` has the value, the delta, `period`, `comparedWith` and `partial` like a sales KPI.
- `pur-open` counts only `DeliveryStatus O` items; cancelled `X` items are not counted.
- `pur-ontime` is delivered-on-time over items promised in the last 90 days up to today; with none due it shows 0% with the caption `nothing due in 90 days`.
- `fin-ageing` returns the five buckets in order, with missing buckets as zero.
- The catalog list has no duplicate id and `pur-categories` is still served by the mock library.
- With butterfly running, every moved widget returns numbers that match a direct butterfly read.

## Out of scope
New butterfly entities (the later phases above), the board overview (synapse-web 18), changing the sales widgets, writing to butterfly.

## Depends on
butterfly 10 and 11 (merged), synapse-web 17 for the KPI card fields (`note`, `partial`).
