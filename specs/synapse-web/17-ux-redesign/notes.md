# Notes

## Left for the owner or later phases
- intent-api sentences use "INR 1,816,237.50" while tables use the rupee sign with Indian grouping (intent-api).
- Day sales draws a zero for days with no sales, which makes a sawtooth; it needs gaps or dimmed closed days (synapse-api data and `@sami/ui` line chart).
- The gauge still shows its value and target in small text under the ring; month-target pace colour is not drawn.
- Heatmap cells and legends, the half-drawn current month bar, compact `89L` labels against full rupee amounts, table row hover.
- AI Mode has no app shell (an earlier phase's test requires full screen). The only exit is a button.
- The Microsoft sign-in button does nothing yet; no forgot-password link.
- The summary strip and the update time are not in the exported PDF. `Updated` is when the web last got an answer, not an SAP posting time.
- `top` on the catalog data endpoint is no longer used by the web.

## Things to know
- A running intent-api, synapse-api and Vite keep old code until restarted (`scripts/dev.sh`). An intent-api started before the `why` merge refuses `sales_why` with `not_answerable_yet`.
- `@sami/ui` has two tests that fail without this phase's changes: `sizes.test.ts` (playground dashboard rows) and `theme-only.test.ts` (inline style in `playground/DashboardDemo.tsx`).
- `tsc -b` in synapse-web reports three `search` errors on links to `/` that were there before this phase.
- RankedList (`@sami/ui`): a long label no longer wraps the value onto its own line.
- Donut: more than six slices group the smallest as Other.
