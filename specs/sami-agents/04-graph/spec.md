# sami-agents/04 graph

## Goal
sami-agents holds a graph the owner maintains (`graph.toml`) that says what relates to what and what counts as unusual, checks it, shows it, and walks it from a mover to the unusual things behind or after it, with the user's own access and no flow written for any one story.

This phase finds facts and returns them as paths with evidence. Choosing which movers to start from, ranking by how much each explains, the unexplained rest, wording and the evaluation are sami-agents 05.

## The graph file
`apps/sami-agents/graph.toml`, read at start by the loader (stdlib `tomllib`); a bad file stops the start with a message naming the entry. Sketch:

```toml
[node.Customer]
source = "metric:sales.customer"

[node.Contract]
source = "record:contract"
anomaly = { kind = "coverage_gap", from = "ValidFrom", to = "ValidTo" }

[node.ProductionOrder]
source = "record:production_order"
anomaly = [
  { kind = "later_than", due = "PlannedEndDate", done = "ActualEndDate", min_days = 3 },
  { kind = "sum_changed", field = "PlannedQuantity", date = "PlannedStartDate", min_percent = 10 },
]

[node.Component]
source = "record:production_component"
passthrough = true

[edge.customer_contracts]
cause = "Contract"
effect = "Customer"
join = { cause = "SoldToParty", effect = "key" }
carries = ["coverage_gap"]
lookback_days = 60
```

- A **node** names its `source`: `record:<type>` (rows from synapse-api's `/records`) or `metric:<metric>.<dimension>` (a member of a split from `/metrics/.../compare`; its only field is `key`). It has none, one or several `anomaly` entries, or `passthrough = true` (a link node that is walked through without being tested, such as a list of components).
- An **edge** is directed, from a `cause` node to an `effect` node, with the `join` that ties their rows (`cause` and `effect` name the field on each side, `key` for a metric node), the anomaly `carries` kinds of the cause that this edge follows, and a `lookback_days` (default 60). The same two nodes may have an edge in each direction when different anomalies travel each way (late supply flows to production; extra demand flows from sales to production to purchases).
- The join field on a `record:` side must be one of that record type's `key_fields` in the synapse-api registry, because a lookup is a `/records` call by that field.

### Anomaly kinds (a fixed list the code understands; a new kind needs code, a new entry of a known kind does not)
| Kind | Parameters | Unusual when | Gets a date `at` |
|------|-----------|--------------|------------------|
| `later_than` | `due`, `done`, `min_days` (default 3) | the `done` date (or today when empty) is at least `min_days` after `due` | `due` |
| `coverage_gap` | `from`, `to` | some days of the window have no row whose `from` to `to` covers them | first uncovered day |
| `sum_changed` | `field`, `date`, `min_percent`, `pad_days` (default 30) | the sum of `field` over rows dated in the window differs from the previous period by `min_percent` or more | none |
| `value_changed` | `min_percent` | the metric value of this member in the window differs from the previous period by `min_percent` or more (the volume and price effects are returned when the dimension has them) | none |

For `sum_changed` the rows are read over both periods padded by `pad_days` and placed by their own `date` field. Change kinds have no date, so the order check below applies between the dated kinds only; that limit is recorded, not hidden.

## Checking and showing
`sami-agents graph check [--graph PATH] [--registry PATH] [--contracts PATH]` prints every problem and exits 1, or prints `ok` and exits 0. It reports: duplicate or unknown node names in an edge; a `source` that is not in the synapse-api registry (`apps/synapse-api/registry.toml`, read as a file, no running service needed); a record field that the drivers or sales contract (`docs/sap/`) does not list for that entity; a join field that is not a `key_fields` entry; an unknown anomaly kind or a missing, unknown or non-numeric parameter; `carries` kinds that no cause node defines; `passthrough` nodes that also have anomalies; nodes with no edge; cycles (listed as information, they are allowed because every walk has limits).

`sami-agents graph show [--mermaid]` prints the nodes (source, anomalies) and the edges (cause to effect, join, carries, lookback), or Mermaid source for a picture.

## Walking the graph
A walk is given the mode, one or more starting `(node, key)` pairs (for a record node also the `key_field`, default the first), a window (`start`, `end`) and its previous period (`compare_start`, `compare_end`), and the user's access token. It reads through a `DataSource` port (a mock for tests; an adapter that calls synapse-api `/records` and `/metrics/.../compare` with the user's cookie, never anything else). Nothing is cached across walks.

| Mode | Starts at | Follows |
|------|-----------|---------|
| `root_cause` | a mover (an effect) | edges whose `effect` is the current node, towards causes |
| `impact` | a node with an anomaly | edges whose `cause` is the current node, towards effects |
| `dependency` | any node | edges either way, no anomaly test: lists the related nodes and keys that exist, read over the widest window the API allows (400 days ending at the window's end) |

Root cause and impact, at each step:
1. Take the distinct join values of the rows reached so far (a metric member is the row `{key}`) and read the next node's rows for each value, over the window widened backwards by the edge's `lookback_days` (root cause) or forwards by it (impact); the previous period for change kinds is the same length directly before the widened window.
2. A `passthrough` node is walked through without a test. Any other node is tested with its anomaly kinds that the edge `carries`; a node with no anomaly is **pruned**: it is not followed and not reported as a cause. `later_than` is judged per row, `coverage_gap` per looked-up key, `value_changed` per member, and `sum_changed` over all the rows reached by the step together (several orders that use one material are one group). The walk continues from the unusual rows (the rows dated in the window for `sum_changed`).
3. The step is kept only if the dated anomalies keep the order: along a root-cause path the cause's `at` is not after its effect's `at`; along an impact path the effect's `at` is not before the cause's.
4. A path ends where there is nothing further, and a walk stops (`truncated = true`) at depth 6, 100 visited `(node, key)` pairs or 200 data calls, whichever comes first. A lookup (node, field, value) is made once per walk. A metric member is looked up in the top 50 changes of its dimension, so a member outside them is not found (recorded as a limit).
- Result: a list of paths; each step has the node, key, the anomaly kind, `at`, the numbers behind it (days late, days uncovered, percent, volume and price effect) and the rows that show it (SAP fields as returned). An empty list is a valid result: "nothing unusual found behind this mover".
- A failure of the data source raises one error for the whole walk; no partial result.

## Acceptance cases
Checks and loader:
- The shipped `graph.toml` passes `graph check` against the real registry and contracts.
- Each problem in the list above is reported by name by a small bad file; several problems are all reported in one run.
- `graph show` lists every node and edge; `--mermaid` is valid `graph LR` text.

Anomaly kinds (unit, on rows):
- `later_than`: 12 days late is unusual; 2 days is not; an open item overdue by 11 days counts to today; an open item not yet due does not.
- `coverage_gap`: a contract that ends 12 July leaves 31 uncovered days in August; a renewal that starts 14 September leaves the same; two contracts back to back leave none.
- `sum_changed`: +23% over the padded periods is unusual at `min_percent = 10`; +5% is not; rows are placed by their own date.
- `value_changed`: -15% at `min_percent = 10` is unusual and returns volume and price effects when the dimension has a quantity.

Walks (unit, with a mock source):
- Root cause stops at a node with no anomaly and does not follow beyond it; a normal delivery is never reported.
- A pass-through node is walked through; the delivery behind a component is found.
- A path whose cause starts after its effect is dropped.
- The same `(node, key)` is not visited twice; a loop in the graph ends; the depth, node and call limits each set `truncated`.
- An edge only follows the kinds it `carries`; two edges between the same nodes in opposite directions carry different kinds.
- Impact mode finds the effects of a late delivery downstream; dependency mode lists related keys with no window.
- A failing source fails the whole walk.

Against butterfly and synapse-api in process (as the earlier phases):
- `august-contract`, window August 2026: from Customer `0000100001` root cause finds Contract `0040000127` with 31 uncovered days; from Product `RM-1002` it finds Production order `0001000417` (14 days late, reason `MATERIAL_SHORTAGE`), behind it Purchase delivery `4500001207` (12 days late); nothing is reported for the May decoys (they lie outside the lookback).
- Impact from delivery `4500001207` reaches production order `0001000417` and then Product `RM-1002` in `august-contract`, and stops at production in `supplier-no-effect` (sales did not move).
- `breakdown-shortfall`, window July to August: from Product `RM-1005` root cause finds Production order `0001000420` with `MACHINE_BREAKDOWN` and no delivery.
- `customer-lost`: from Customer `0000100005` nothing is found (its contract covers the window).
- `price-cut`: from Product `RM-1001` nothing is found behind it.
- The held-back scenarios are not read by any development test.

## Out of scope
Choosing movers, ranking, the explained share and unexplained rest, sentences and the model (sami-agents 05); purchase metrics and their scenario checks (added with the purchases entries in the synapse-api registry, in 05); any new anomaly kind beyond the four; a command that runs a walk from the terminal; caching; writing to the graph from the app; a visual editor.

## Depends on
synapse-api 09 (registry, `/records`, `/metrics`), butterfly 09 scenarios, `docs/sap/` contracts, `docs/ai-analysis.md`.
