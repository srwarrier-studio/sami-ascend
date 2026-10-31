# butterfly/09 scenarios

## Goal
Butterfly can serve several different mock sales stories, each with a written ground truth, so the AI analysis is built and tested on more than the one story (`august-contract`) it was first shaped by. Two scenarios are held back until the final evaluation.

## Behavior
- `BUTTERFLY_SCENARIO` chooses the story served with `BUTTERFLY_SEED=story`. The default is `august-contract`, which must stay byte-for-byte what butterfly 08 serves (every existing test keeps passing).
- A scenario is a small description (a dataclass) of events applied to the same base history (14 months of steady sales, one contract per customer, a monthly purchase order per raw material, a monthly production order per product). An event is one of:
  - a **contract end**: customer, last valid date, optional renewal date, and the effect on that customer's orders (stop, or a reduced share) until renewal;
  - a **supply delay**: raw material, days late, month; with an optional effect on its product's orders (none, or a share dropped while the product is short);
  - a **production delay**: product, days late, reason, month; with the same optional effect;
  - a **price change**: product, factor, from date (volume unchanged, net amounts change);
  - a **customer loss**: customer, from date, with no contract or other event behind it;
  - a **cancellation spike**: customer, share of orders cancelled (status `X`) in a window.
- Scenarios:

  | Name | Events | Written ground truth |
  |------|--------|----------------------|
  | `august-contract` | the butterfly 08 story | as in butterfly 08 |
  | `price-cut` | Steel rod 12mm price down 15% from 2026-08-01 | August sales value falls because of price on that product; volume is unchanged; no contract, supply or production event |
  | `supplier-no-effect` | Doosan coil 12 days late and Steel plate production 14 days late in July, with no change in orders | no drop in sales; the delays exist and no effect on sales is found |
  | `customer-lost` | Eastern Castings stops ordering from 2026-08-10, contract still valid | Eastern is the biggest mover; no contract, supply or production event explains it |
  | `breakdown-shortfall` | a machine breakdown delays Bearing 6204 production by 10 days in July, and bearing orders from three customers drop by half until 2026-08-15 | the production order with reason `MACHINE_BREAKDOWN`; no supplier delay is involved |
  | `quiet-month` | none | no month differs from the normal level by more than 5% |
  | `two-causes` (held back) | Deccan's contract ends 2026-07-20 and Cauvery's copper rod delivery is 10 days late with copper wire orders dropping | both causes found, each tied to its own customer or product |
  | `cancellations` (held back) | Cauvery cancels 40% of its orders (status `X`) in August | the cancelled orders, not a contract or supply event |

- Each scenario has a ground truth file `scenarios/<name>.json`: the month to ask about, the expected size of the change (a range), the causes that must be found (with their keys: contract, order, delivery), the factors that must not be blamed, and whether anything should be left unexplained. Held-back scenarios are marked `"holdout": true`; development and tuning of the agent do not read them, only the final evaluation does.
- Order sizes are scaled by month length and every number comes from fixed arithmetic, as in butterfly 08; a scenario never changes data before its first event.
- The runner stops with a message for an unknown scenario name; the README lists the scenarios and their ground truth.

## Acceptance cases
- `august-contract` equals the butterfly 08 data exactly.
- For each scenario, the facts in its ground truth hold in the data (the sales change within its range, the events exist with the stated keys and dates, the not-to-blame events exist and have no effect, and a quiet scenario has no month beyond 5% of normal).
- The base history before the first event is identical across scenarios.
- The scenario list, the held-back flags and the ground truth files agree.
- The sales and drivers contract tests pass for every scenario.

## Out of scope
The agent, synapse-api endpoints, writes, failure modes.

## Depends on
butterfly 08, `docs/ai-analysis.md`.
