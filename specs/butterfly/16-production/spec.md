# butterfly/16 production

## Goal
Butterfly serves what the shop floor did, as the SAP service will: a read-only OData V4 service `ZUI_PRODUCTION_O4` with confirmed output, scrap and downtime per work center and shift, and four summaries, specified in `docs/sap/production-contract.md`, with data that follows from the production orders butterfly already holds.

## Why
Six of the seven Production widgets (output, equipment effectiveness, output against plan, downtime by cause, scrap by reason, output by line and shift) are fixed numbers in synapse-api's `mock_library.json`. The seventh, open production orders, can already be read from the drivers service. Butterfly is the one source of data, so the shop floor has to exist there first, as a contract the ABAP team can build from.

## Behavior
- **Contract first.** `docs/sap/production-contract.md` (written with this spec) defines the service, `ProductionConfirmation`, `WorkCenterDowntime` and four summaries, with fields, codes, joins and SAP sources. Consultant questions 27 to 33 are in `consultant-questions.md`. Every example in the contract is a real response and is checked by a test.
- **Same conventions** as the other services: JSON only, query options, error shapes, paging rules, `CompanyCode` on every row, read-only, `$expand` refused, one row by key not supported; summaries are SQL views like in butterfly 13 and 14.
- **Master data.** Each company gets three work centers (lines) in its plant; shifts, scrap reasons and downtime causes are codes.
- **One story.** Everything is generated from the existing production orders so every number can be explained:
  - A completed order is confirmed on each working day (Monday to Saturday) from its planned start to its actual end, one confirmation per day on one work center and shift; the yields add up exactly to the order's confirmed quantity, the targets to its planned quantity.
  - Scrap is a deterministic share (about 0.5% to 4%) of the yield with a deterministic reason.
  - Every order has a changeover stoppage on its first day; each line has a maintenance stoppage once a month; an order with a delay reason (`MACHINE_BREAKDOWN`, `MATERIAL_SHORTAGE`) has a stoppage of that cause of 8 hours for each day it ran late; about one order in eight has a short other stoppage. Every stoppage is posted on a day the company has confirmations, so the daily summary adds up.
  - Orders that have not started (the released orders of next month) have no confirmations.
  - Value is the quantity at the standard price already used for stock (butterfly 14).
  - Everything is deterministic for a seed and today's date.
- **Tables and views.** New tables `work_center`, `production_confirmation`, `work_center_downtime`; the summaries are SQL views (one `.sql` file each); an older database without the data is rebuilt (the layout version changes) and keeps API orders.
- Nothing already served changes.

## Acceptance cases
- Every field of every entity matches the contract tables; the contract examples match the real responses on both stores.
- For every completed order, the yields add up to `ConfirmedQuantity` and the targets to `PlannedQuantity`; orders that have not started have no confirmations.
- Every delayed order has a stoppage of its cause with 8 hours per day of delay.
- The four summaries equal hand totals over their source rows for a `CompanyCode` filter too; the daily downtime hours equal the sum of the downtime events of that day; no event is posted on a day without confirmations of its company.
- The database and the lists answer the same for filters, ordering and paging.
- `BUTTERFLY_SEED=small` serves empty production; an unknown entity is `404`.
- Starting on an older database adds the production data and keeps API orders.

## Out of scope
The synapse-api widgets (synapse-api 14), real shift calendars, machine-level data, OEE as a field (a consumer works it out), writes, authentication.

## Depends on
butterfly 14 (standard prices, plants) and 15 (branch base).

## Open questions for the owner
1. Is one confirmation per shift and work center the right grain for SAP (consultant question 28)?
2. Output is in value at standard price so kilos and pieces can be added; is that acceptable for the "output" widgets?
