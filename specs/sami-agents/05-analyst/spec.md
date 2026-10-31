# sami-agents/05 analyst

## Goal
A user asks "why did sales fall in August?" or "why did purchases rise in September?" and gets back what moved, what the data shows behind it, how much of the change that explains and how much it cannot explain, with evidence for every statement. It works for any metric in the synapse-api registry, uses only our own services and the user's own access, and needs no AI model.

## What is new and what is reused
- Reused: the metric reads (`/metrics/.../compare` and `/month`), the graph and the walk (sami-agents 04), the data port.
- New: purchases in the registry and the graph, one more anomaly kind, reading the question, choosing movers, assembling and ranking findings, the answer blocks and wording with their checks, a route, and an evaluation tool.
- Change of plan: this phase includes reading the question (metric, direction, month). sami-agents 03 (level 2, "what were sales for August") will reuse that reader and the answer blocks and add a figure with a trend. 05 no longer depends on 03.

## Behavior
### Purchases in the registry and the graph
- `apps/synapse-api/registry.toml` gets the `purchases` metric on the drivers service: `by.day` `PurchaseSummaryByDay`, `by.supplier` `PurchaseSummaryBySupplier` (key `Supplier`, name `SupplierName`), `by.material` `PurchaseSummaryByMaterial` (key `Material`, name `MaterialDescription`, quantity `TotalQuantity`, unit `QuantityUnit`), measure `TotalNetAmount`, date `OrderDate`, currency `Currency`, count `OrderCount` on the day entity.
- `graph.toml` gets a metric node `PurchasedMaterial` (`metric:purchases.material`, `value_changed`) and an edge from `PurchaseDelivery` to it (join `Material` to `key`) that carries `sum_changed` and `set_changed`. Starting from a purchased material, the walk then reaches the production orders that use it and the sales of the product behind them through the edges that already exist.
- `later_than` gets an optional `reason` field name (`DelayReason`) whose value is carried in the numbers. One new anomaly kind, `set_changed` (parameters `field`, `date`, `pad_days` default 30): the set of distinct values of `field` among rows dated in the window differs from the previous period; the numbers are `new` and `gone` (sorted lists). `PurchaseDelivery` gets `{ kind = "set_changed", field = "Supplier", date = "OrderDate" }`. `graph check` knows the kind and validates its fields.
- Root cause gains one rule in the walk (from sami-agents 04): an edge whose `shows` is not empty is only followed when the kind found at its effect is one of them (a starting mover has no kind and follows every edge). This keeps a change of supplier from being "explained" by production plans.

### Reading the question
`QuestionReader` turns the text into `Question(metric, direction, month, intent)` with plain rules and `apps/sami-agents/understanding.json` (the owner edits it like `aliases.json`): words that name each registered metric, words for rise and fall, month names.
- Intent: only "why" questions about a metric and a month are answered in this phase: a metric word, a rise or fall word (or "change"), a month with an optional year. Month names without a year mean the latest finished month of that name. The month is compared with the month before it.
- A question it cannot read gets a plain reply saying what it can answer ("Ask why a metric rose or fell in a month, for example: why did sales fall in August?"), never a guess. A month that has not finished is refused with the reason.
- `understanding.json` is checked against the registry: every registered metric needs words (a test fails when a metric is added without them).

### Measuring and choosing movers
For the metric and the two months, per currency (this phase analyses the first and says so when there are more):
1. `compare` totals: current, previous, change, change percent. The change is **significant** at `SIGNIFICANT_PERCENT` (default 5) or more.
2. For each dimension of the metric (sales: customer and material; purchases: supplier and material) `compare` by that dimension with `top` 10. A **notable mover** is a member whose own change is at least `MOVER_MIN_PERCENT` (10) of its previous value and whose change is at least `MOVER_MIN_SHARE` (2) percent of the previous total. For a "fall" question the movers that fell are the findings and the ones that rose are the **offsets**; for "rise" the reverse; for "change" both are findings.
3. A mover on a dimension with a quantity (material) also reports its volume and price effect. When the price effect is at least `PRICE_MAJORITY` (50) percent of the member's change the finding is a **price finding** ("mostly price, not volume") and needs no walk.
4. Every notable mover whose dimension has a node in the graph (`metric:<metric>.<dimension>`) is walked in root-cause mode, as a start with the month as the window and the previous month as its previous period. A mover that is not notable is **never walked**: a late delivery behind a product whose sales did not move is not a cause of anything.

### Findings, ranking and the unexplained rest
- A finding is a notable mover (its amount, percent, share of the total change, volume and price effect) with zero or more cause paths from the walk (each step: what, key, date, numbers, evidence rows). Graph nodes may name an `id` field (`id = "PurchaseOrder"`) so a step can say which document it is.
- Findings are ranked by share of the total change, largest first. Within a dimension the shares add up (offsets included, with their sign); shares of different dimensions describe the same change from different sides and are **never added**.
- A finding counts as **explained** when it is a price finding, or has a cause path with a step of a kind that says why (`later_than`, `coverage_gap`, `set_changed`) or with at least two steps (a chain that reaches another part of the business). A single `sum_changed` or `value_changed` step only restates the movement (a bigger order, a fall in sales) and does not explain it; each anomaly kind says which it is (`explains`).
- Explained share: for each dimension, the sum of the shares of its explained findings; the answer reports the largest of these as "at least X% explained" and `100 - X` as the unexplained rest. No findings with causes means the unexplained rest is 100 and the answer says "no cause found in the data we hold".
- The walk's `truncated` flag and the single-currency limit are listed under `limits` in the answer.

### The answer
`POST /v1/agents/analyse` with `{question}` (1 to 500 characters), cookie auth with the management or admin role, returns JSON:
- `question`: the metric, direction, month and previous month as understood, so a wrong reading is visible.
- `blocks`: an ordered list drawn later by synapse-web: `text` (the headline and a sentence per finding), `trend` (the last 6 months of the metric from `/metrics/.../month`, the two months marked), `table` (the movers of each dimension with their amounts, percents, shares, volume and price effects) and `evidence` (for each cause path, the rows behind each step as SAP returned them).
- `analysis`: the machine-readable result: headline figures, `significant`, findings with their paths, offsets, `explained_percent`, `unexplained_percent`, `limits`, and for each finding `causes`, a list of generic tags `{source, kind, key}` taken from the steps (for example `{source: "record:production_order", kind: "later_than", key: "0001000417"}`; the key is the node's `id` value for a per-row kind and the looked-up key for a group kind; a price finding gives `{source: "metric:purchases.material", kind: "price_effect", key: "RAW-2002"}`). The analyst knows nothing about the ground truth vocabulary; the evaluation maps the truth causes onto these tags.
- A label `Mock data (butterfly)` is added when `SAP_IS_MOCK` is true (the default until the real views exist).
- Errors: unreadable question is `200` with the help text and no findings; data unavailable is `503 DATA_UNAVAILABLE`; the cookie and role rules of the chat route.

### Wording and its checks
The text is built from templates, one per finding kind, filled only from the analysis (`coverage_gap`: "had no valid contract for N days from DATE (contract NUMBER ended DATE)"; `later_than`: "was N days late (promised DATE, delivered DATE)" with the reason when there is one; `sum_changed`: "rose N% over the period"; `set_changed`: "moved from SUPPLIER to SUPPLIER"; price and volume sentences). The verbs are "coincided with", "contributed to", "behind it", never "caused". Every figure, date and name in the text is taken from the analysis; a test builds every sentence from random analyses and checks that each number, date and name in it appears in the analysis.

### Optional local model (off by default, nothing leaves the machine)
Two hooks behind ports, both used only when `OLLAMA_MODEL` is set, both checked:
- a question reader fallback, used only when the rules cannot read the question: the model returns JSON for `{metric, direction, month}` which is accepted only when the metric is registered, the direction is one of the three and the month is a valid `YYYY-MM` that has ended; anything else is treated as unreadable;
- a rephrase of the headline sentence, accepted only if every number, date and name in it is in the analysis and it adds none; otherwise the template text is kept.
No other model use exists. A test checks that tracing is off at start (`LANGSMITH_TRACING` and `LANGCHAIN_TRACING_V2` false) and that the analyst only calls the configured synapse-api (and Ollama when set); there is no other outbound client in the code path.

### Evaluation
`sami-agents analyst-eval [--final]` runs the analyst in process against butterfly through synapse-api (as the walk tests do) for every scenario whose ground truth file is not held back, one question each (`evals/analyst.json`: scenario, question text, from the ground truth month), and prints per scenario and in total: causes found, causes missed, causes **invented** (a cause tag that is neither in the truth nor excused), blamed `not_blame` items, the headline change against the range, whether "unexplained" matches, and PASS or FAIL. A confident wrong cause is a FAIL even when every true cause is also found. `--final` also runs the held-back scenarios; development runs and every test never read them.
- A scenario passes only when: every truth cause is found, no `not_blame` item and no invented cause appears, the change is inside the truth range, `unexplained` is honoured (when the truth says unexplained, the answer's unexplained rest is at least 50, or it names the truth's `biggest_mover` as its largest finding), and a truth with no causes and a small change gets "no significant change" or no findings.
- Misses that are expected today and must be reported as misses, not hidden: `cancellations` (the summaries leave cancelled orders out and the graph has no sales-order record), and the `supplier_switch` split by material only if `set_changed` does not find it. The report prints what a missing graph entry would be (the how-to in `docs/graph-maintenance.md`).

## Acceptance cases
Reader and thresholds (unit, no data):
- "why did sales fall in August", "Why did purchases go up in September 2026?", "what made revenue drop last month" read correctly; "show me sales" and "why is the sky blue" are unreadable and get the help text; the current month is refused; a registered metric without words fails the registry test.
- A mover that moved 9% is not notable, 11% is; a mover with 1% of the total is not, 3% is; a price effect of 49% of the change is a volume finding, 50% a price finding.
- Ranking: findings are ordered by share, offsets keep their sign, shares from two dimensions are not added, explained is the larger dimension's covered share, no cause paths give 100 unexplained.
- Wording: every sentence passes the check; a rephrase that adds a number, a date or a name is dropped; a model that returns bad JSON, an unknown metric or a future month leaves the question unreadable.

Walk and graph additions (unit):
- `set_changed` finds a new and a gone supplier and nothing when the set is unchanged; `graph check` passes with the purchases entries and reports a missing field of the new kind; the root-cause `shows` rule stops a `set_changed` hit from following the production edge and does not stop a starting mover.

Scenarios through butterfly and synapse-api in process (development scenarios only):
- `august-contract`: significant fall of about 14.5%; finding Acme about 80% with contract `0040000127`; finding Steel plate with production order `0001000417` and delivery `4500001207`; no May decoy; explained at least 70%.
- `price-cut`: a price finding on Steel rod, no cause paths, no invented cause.
- `supplier-no-effect`: no significant change and no findings; the late delivery and production order are not reported as causes.
- `customer-lost`: Eastern Castings is the largest finding, no cause path, unexplained 100.
- `breakdown-shortfall`: month July; total change small, finding Bearing 6204 with production order `0001000420` (`MACHINE_BREAKDOWN`) and no delivery.
- `quiet-month` and `quiet-purchases`: no significant change and no findings.
- `purchase-price-rise`: price finding on Steel coil; `stock-up`: finding Copper rod with `purchase_quantity_change` and nothing upstream, unexplained; `demand-surge`: Steel coil with the chain production order then Steel plate sales (`demand_growth` on `RM-1002`).
- All development scenarios pass `analyst-eval`; `--final` prints the held-back results (two-causes, cancellations, supplier-switch, double-cause) and its misses without anyone tuning against them first.

## Out of scope
Level 2 figures and trend answers (03), drawing the blocks (synapse-web 12), impact and dependency questions in natural language, other periods than a month, several currencies, a record type and kind for cancelled orders, company filtering, a terminal command to ask a question, caching, any model use beyond the two hooks.

## Depends on
sami-agents 04, synapse-api 08 and 09, butterfly 09 and 10, `docs/ai-analysis.md`, `docs/graph-maintenance.md`.
