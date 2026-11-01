# intent-api/03 answers

## Goal
`POST /v1/intent/answer` takes a manager's question and returns the answer built from the scenario Laya read: a sentence with the real figure and, only where the scenario needs one, a chart or a list. The answer comes from the scenario key and the data it needs, never from keyword matching.

## Why
Phase 02 made the reading good (`intent-tuned-2`: 73 of 80 answerable questions exactly right, 1 harmful answer in 121). In AI Mode the answer still comes from sami-agents' keyword matcher, so "to whom did we sell the most in June" is read as `sales_top_customers` (100%) and answered with "Most overdue accounts". The reading is right and the answer ignores it. Not every answer needs a chart: a value is a sentence, a trend is a chart.

## Behavior
- A response table, `answers.toml` next to `scenarios.toml`, has one entry per scenario key: `response` (`value`, `compare`, `trend`, `ranking`; `why` is not here), the `metric` of the synapse-api registry, for a compare `against` (`previous` or `last_year`), and for a ranking the `by` dimension (`customer`, `supplier`, `material`). A key with no entry is read but not answered (`not_answerable_yet`). Changing what an answer looks like is a change in this file, not in code.
- Response kinds and the blocks they return (the same JSON blocks sami-agents returns, so synapse-web draws them already):

| Response | Scenario keys | Blocks |
|---|---|---|
| `value` | `sales_value`, `purchases_value` | `text` only: one sentence with the figure for the period |
| `compare` | `*_compare_previous`, `*_compare_last_year` | `text` only: both figures and the change |
| `trend` | `*_trend` | `text` (direction) and `trend` |
| `ranking` | `*_top_customers`, `*_top_suppliers`, `*_top_materials` | `text` (the leader and its share) and a ranked `table` |

- Period (the only slot in this phase), read by rules from the question and never by Laya: a month name, "last month", "this month", "last year", a year; none given means the last finished month. A question that names more than one period, or a period synapse-api cannot answer, is refused with `reason: "period_not_supported"` and the periods it could read. Customer, supplier and material names (the `entity` slot) are phase 04; a question that names one is answered for the whole company and says so in the sentence.
- Data comes only from synapse-api, with the caller's cookie forwarded: `GET /v1/synapse/metrics/{metric}/month` for a value and a trend, `/compare` for comparisons and (with `by` and `top`) for rankings. Amounts are written as in sami-agents (`INR 6,480,000`, mixed INR and USD kept apart per currency, as the metric returns them).
- Honest results: no data for the period gives a sentence saying so and no chart; synapse-api down gives `503` with `cannot_fetch_now`; a Laya failure keeps `cannot_classify_now`; every refusal of phase 01 stays and is still logged to `unanswered.jsonl`.
- The answer carries the reading (domain, scenarios, probabilities) so synapse-web can keep showing how the question was understood.
- `why` scenarios are out of this phase: the answer says they come from the analyst and returns the reading only.

## Acceptance cases
- Each response kind has a test against a mock synapse-api: the sentence has the figure and the blocks are exactly those in the table (a `value` answer has no chart).
- "to whom did we sell the most in June" returns a sentence naming the leader and a ranked table of customers for June (never receivables).
- "how much did we sell in June" returns one sentence and no chart; "sales trend this year" returns a sentence and a trend.
- A combined question ("top customers in June and the trend") returns both answers in order, one per scenario. A scenario that another one `covers` is dropped as before ("sales in June and how that compares" is one compare answer, which already has the figure).
- A scenario with no `answers.toml` entry, a period not supported, no data and synapse-api down each give the specified result, not a wrong figure.
- `answers check` fails on an entry for an unknown scenario key, an unknown response kind or a ranking without `by`.
- No answer text is produced by a model: sentences come from templates in the code.

## Out of scope
The `entity` slot (a named customer, supplier or material), `why` answers, wiring AI Mode to the new route (phase 04), chart types beyond text, trend and table, Docker, forecasts, margins and other domains.

## Depends on
`intent-api/02` (merged), synapse-api metrics routes (`/metrics/{metric}/month` and `/compare`), the token cookie check already in intent-api.

## Open items for the owner
1. "Invoiced" is not sales in the registry (sales are orders). Should "how much did we invoice" read as `sales_value`, or wait for an invoice metric from SAP?
2. Mixed INR and USD: one sentence per currency, or the metric's main currency first and the other after?
3. A ranking shows the top 5 (default) or 10?
