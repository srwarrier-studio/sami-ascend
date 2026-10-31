# butterfly/08 driver-data

## Goal
Butterfly serves the drivers service from `docs/sap/drivers-contract.md` (customer contracts, supplier deliveries, production orders and their components), with 14 months of sales history and a built-in story that explains why sales fell in August 2026. The AI analysis (`docs/ai-analysis.md`) can then be built and tested before the SAP views exist.

## Behavior
- A second OData service next to the sales one, on the contract's root path `/sap/opu/odata4/sap/zui_drivers_o4/srvd_a2x/sap/zdrivers/0001/`, with four read-only entity sets: `SalesContract`, `PurchaseDelivery`, `ProductionOrder`, `ProductionOrderComponent`. They support `$filter`, `$select`, `$orderby`, `$top`, `$skip` and `$count` exactly as the sales summaries do; `$expand` and any other option return `400` in the existing error format. Writes are not served.
- Entities, field maps and an in-memory `DriverRepo` follow the existing layers (`domain/entities`, `domain/repositories`, `infrastructure/memory`, `application/filter/fields.py`). The list use case is the one the summaries already use.
- Story seed: `build_story_seed(today)` returns sales orders for every working day from 2025-09-01 to `today` (5 customers, 6 materials, 3 to 6 orders a day, fixed arithmetic only, no random numbers, order sizes scaled by the length of the month so a normal month always has the same volume) plus the driver rows below. `build_seed` (30 orders) is unchanged and is what the tests use. The runner picks the seed with `BUTTERFLY_SEED` (`story` by default, `small` for the old one; anything else stops the start with a message).
- The story, which every number below must come out of:
  - **Contract.** Acme Industries (`0000100001`, the biggest customer, about a fifth of sales) has contract `0040000127` valid 2025-07-13 to 2026-07-12 (renewing `0040000071`), status `E`. It is renewed by `0040000163` valid 2026-09-14 to 2027-09-13 (status `A`). From 2026-07-13 to 2026-09-13 Acme places only a few small spot orders. The other four customers have an active contract all through the period.
  - **Supply.** Doosan Metals Pvt Ltd (`0000200001`) delivers Steel coil (`RAW-2002`) on `4500001207`: promised 2026-07-14, delivered 2026-07-26 (12 days late). Its other deliveries are on time or within 2 days. A second supplier, Kalyani Wire Industries (`0000200002`), delivers Copper rod (`RAW-2003`) 4 days late on one order in May 2026, with no effect on sales.
  - **Production.** Production order `0001000417` for Steel plate 5mm (`RM-1002`) is planned 2026-07-06 to 2026-07-20 and finishes 2026-08-03, reason `MATERIAL_SHORTAGE`, with `RAW-2002` as a component. Production order `0001000408` for Bearing 6204 (`RM-1005`) finishes 6 days late in May 2026, reason `MACHINE_BREAKDOWN`, with no effect on sales. Every other product has a monthly production order that finishes on time.
  - **Effect on sales.** Orders for Steel plate 5mm from the other customers are about 40% lower from 2026-07-20 to 2026-08-31 and normal again from September. Everything else moves by small, fixed amounts.
  - **Ground truth.** August 2026 sales are 13% to 16% below July 2026 (measured 14.5%, ₹75.7 lakh to ₹64.8 lakh). The fall splits into three parts that add up to 100%: Acme's lost sales about 80%, the steel plate shortage on the other customers about 38%, and an offset of about -18% because the rest of the business grew slightly. `docs/ai-analysis.md` section 7 has the figures.
- The README says the data is invented and describes the story.

## Acceptance cases
- Contract: `drivers-contract.md` tests pass; every example in it can be reproduced by a query against the story seed.
- Each entity set: lists with `$count`, filters on every filterable field type (string, date, decimal), `$select` order as in the field tables, `$orderby`, `$top` and `$skip`, nullable fields come back as `null` and match no comparison.
- `$expand`, `$apply` and unknown options give `400`; a write gives `405` in the error format.
- Story: the contract dates, the three deliveries and two production orders above exist exactly; the monthly totals and shares in the ground truth hold; the seed is identical on every run and for any `today` after 2026-09-30 the history up to 2026-09-30 does not change.
- Existing sales tests are untouched and pass; `BUTTERFLY_SEED=small` serves the old seed.

## Out of scope
Writes, failure modes (butterfly 04), the SAP views, synapse-api endpoints and the agent that uses this data.

## Depends on
butterfly 03, `docs/sap/drivers-contract.md`, `docs/ai-analysis.md`.
