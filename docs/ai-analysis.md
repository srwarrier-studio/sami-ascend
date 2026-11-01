# AI analysis: answering "why" questions

Status: built through the analyst (2026-10-31): metric layer and registry (synapse-api 08, 09), purchases and scenarios (butterfly 09, 10), the graph and its walk (sami-agents 04) and the analyst with its evaluation (sami-agents 05). Level 2 figure answers (sami-agents 03), drawing them in AI Mode (synapse-web 12) and the Laya case reader (sami-agents 06) are done; the case tree (sami-agents 07) is next.

## 0. Scope: any metric, nothing leaves the building

The questions are "why did sales fall in a month" and "why did purchases rise in a month", and the same machinery serves any metric that is registered. The contract, supply and production flows below are examples of what the graph can hold, not flows the code knows. Nothing is written for one story: what is measured comes from the metric registry, what is related comes from the graph, and what counts as unusual comes from a short list of generic anomaly kinds.

The research facility does not allow external or cloud AI, and nothing is sent to one. Every figure comes from code over data held in butterfly or SAP, inside our own services. A local model (Ollama) may help read the question and rephrase the answer, is checked against the findings, and is optional. Tracing or telemetry libraries pulled in by the agent framework (`langsmith` is installed with LangGraph) must be off, and a test checks that.

## 1. What management asks

| Level | Example | What it needs | Status |
|-------|---------|---------------|--------|
| 1. Show me | "show me sales and top customers" | pick widgets | done (`sami-agents` keyword search) |
| 2. Tell me | "What are the sales for August?" | metric and period from the question, a real figure, a sentence, a trend chart | done (sami-agents 03) |
| 3. Why | "Why did sales drop in August?" | find where the change is, traverse the related things for what happened there, rank by effect, explain with evidence | this document |

A level 3 answer looks like: "Sales fell 14.5% from July to August ($94.7k to $80.9k). About $11.0k of the fall is Harborline Nutrition LLC, whose sales contract ended on 12 July and was not renewed until 14 September. About $5.2k is Piperine extract 95% sold to other customers: Deccan Agro Growers Cooperative delivered Black pepper, whole 12 days late (promised 14 July, delivered 26 July), which delayed production order 0001000417 by 14 days. The other customers together bought about $2.5k more, which offsets part of it."

## 2. Principles

1. **Code finds facts, a model never invents them.** Every figure, date and name in an answer comes from a query result. A model may help understand the question, and may polish wording, but a check rejects any name, number or date that is not in the findings.
2. **Say what the data shows.** Findings are "coincided with" and "contributed to", not proof of cause. Each finding lists its evidence (document numbers, dates, amounts). The answer says how much of the change is explained and how much is not, and "no cause found in the data we hold" is a valid answer.
3. **Use the user's own access.** Every check runs with the signed-in user's session, so the answer only contains what that person may see.
4. **Mock data is labelled** while the data comes from butterfly.
5. **No flow is written for one question.** What is checked and in what order comes from a description of the data (the graph below), not from code written for a particular question. Adding a data source means editing that description.

## 3. Two parts: a metric layer and an entity graph

A graph suits questions about *relationships* and does nothing for questions about *numbers*. So the work is split.

| Part | Answers | How |
|------|---------|-----|
| **Metric layer** | "sales for August", "top five customers", "this month against last", "where did the change come from" (split by customer, material, month; volume against price) | grouping and comparing over the sales data, in synapse-api; no graph |
| **Entity graph** | "why did it happen", "what does X affect", "what depends on what" | traversal over related things across systems |

The metric layer finds *where* a change is (Harborline fell, Piperine extract fell). The graph explains *why it happened there*.

### The entity graph

A typed graph kept as a file in `sami-agents` that the owner maintains.

- A **node type** is a kind of thing: Customer, Contract, Product, ProductionOrder, RawMaterial, PurchaseDelivery, Supplier. It names where its rows come from (a synapse-api source) and its key.
- An **edge** says how two node types relate, and the fields that join them: "a Customer has Contracts, joined on `SoldToParty`".
- An **anomaly** says what "something happened" means for a node type, as a choice from a fixed list of kinds that the code understands (`ended_in_window`, `later_than_promised`, `finished_after_plan`, `value_fell`), plus the fields to look at. The owner picks a kind and fields; a new *kind* needs code, a new anomaly of an existing kind does not.

```
Customer ──has──> Contract                      anomaly: ended_in_window (ValidTo)
Customer ──buys──> Product
Product ──made by──> ProductionOrder            anomaly: finished_after_plan (PlannedEndDate, ActualEndDate, DelayReason)
ProductionOrder ──uses──> RawMaterial
RawMaterial ──bought on──> PurchaseDelivery     anomaly: later_than_promised (PromisedDeliveryDate, ActualDeliveryDate)
PurchaseDelivery ──from──> Supplier
```

The file is TOML (readable with the standard library, comments allowed). An abbreviated sketch:

```toml
[node.Customer]
source = "sales-by-customer"
key = "SoldToParty"

[node.Contract]
source = "SalesContract"
key = "SalesContract"
anomaly = { kind = "ended_in_window", field = "ValidTo" }

[edge.customer_contracts]
from = "Customer"
to = "Contract"
join = { Customer = "SoldToParty", Contract = "SoldToParty" }
```

### Three ways to traverse the same graph

| Mode | Question | Start | Direction |
|------|----------|-------|-----------|
| Root cause | "why did sales fall in August" | the biggest movers from the metric layer | upstream, through anomalous nodes only |
| Impact | "what did Deccan Agro's late delivery affect" | a node with an anomaly | downstream |
| Dependency | "which suppliers feed what Harborline buys" | any node | either way, no time window |

How the root-cause walk goes:

1. **Measure and split** the change with the metric layer, by every dimension available, and keep the top movers.
2. **Expand** each mover along its edges. At every node fetch its rows for the time window and test its anomaly.
3. **Prune.** Continue only through nodes that show an anomaly. A normal delivery is never followed or explained.
4. **Check order.** Along a path the cause must come before its effect (late delivery, then late production, then the sales dip).
5. **Rank** paths by how much of the change their mover explains, and show the unexplained rest.
6. **Write** the answer from the paths with a template (a model may rephrase), and **validate** every name, date and number against them.

Graph traversal is breadth-first with a limit on depth, nodes and calls, so a question always stops.

## 4. Where each part lives

| Part | App | Notes |
|------|-----|-------|
| Contract for the new data | `docs/sap/drivers-contract.md` | source of truth for butterfly, synapse-api and the SAP consultant |
| Mock SAP data with several scenarios | `butterfly` | `BUTTERFLY_SCENARIO`, each with a ground truth |
| Metric layer: compare periods, split by a dimension, top N | `synapse-api` | read endpoints, generic, cached 5 minutes like the others |
| Event reads: rows of a node type for a key and a window | `synapse-api` | one generic read, not one endpoint per story |
| The graph file, its loader and checker, the traversal | `sami-agents` | the owner edits `graph.toml`; `sami-agents graph check` validates it |
| Question understanding (metric, period, mode, start) | `sami-agents` | rules first; a model only if it measures better |
| Showing the answer (text, chart, evidence) | `synapse-web` | JSON blocks drawn with the existing widgets |
| SAP views for the new entities | SAP team | from the contract |

## 5. Maintaining the graph

The owner maintains `graph.toml`. A short how-to (`docs/graph-maintenance.md`) is written when the loader exists. The workflow it will describe:

1. Add a node type (name, source, key) and the edge that connects it.
2. Optionally add an anomaly of an existing kind.
3. Run `sami-agents graph check`: it reports unknown node names in edges, unknown fields, missing sources, orphan nodes, edge loops without a limit, and anomaly kinds that do not exist. It also checks every source and field against the contracts in `docs/sap/`.
4. Run `sami-agents graph show` to see the graph as a picture or table.
5. Add a scenario to butterfly (or a real past case) with the expected findings and run the evaluation.

Where possible edges come from SAP master data (bills of material, supplier lists), which exists even when no recent order does, and not only from recent transactions.

## 6. The model's role and its limits

- Understanding a question (metric, period, why, what is affected) is a small job. Rules cover most of it; a small model can be tested on phrasing from other people.
- Turning findings into a good paragraph is easy with a template, and a better paragraph needs a stronger model. Small models (up to 3B) invent details when writing freely, so they may only rephrase and are validated.
- A local-only deployment limits quality. Using a hosted model sends business data off the machine, a management and security decision. The design works without a model.

## 6a. How we will know it works, and that it generalises

Butterfly serves several scenarios, each with a written ground truth (the causes that must be found, what must not be blamed, and what must be reported as unexplained):

| Scenario | What happened | Right answer |
|----------|--------------|--------------|
| `august-contract` (the first story, section 7) | contract expired, supplier late, production late | Harborline's contract; pepper shortage through production and supplier; offset by growth elsewhere |
| `price-cut` | a product's price is cut, volume unchanged | the metric layer shows price, not volume; no event explains it |
| `supplier-no-effect` | late delivery and late production, but sales do not move | no sales drop; if asked about impact, production was delayed and no sales effect is found |
| `customer-lost` | a customer stops ordering with its contract still valid | the customer is the biggest mover; no cause found in the data |
| `breakdown-shortfall` | a machine breakdown delays a product and its sales fall | production order with the breakdown reason, no supplier involved |
| `quiet-month` | normal variation only | no significant change |
| two held back until the final test | contract and supplier on different customers and products; a cancellation spike | as written in each |

An evaluation run reports causes found, causes invented and causes missed, and refuses to count a confident wrong answer as a pass. Questions are tested with phrasing written by other people, and real past drops with known causes replace the mock scenarios when the SAP views exist.

## 7. The first scenario, `august-contract` (butterfly 08)

> Data note (butterfly 12): the story belongs to company `INA1` (Sami-Sabinsa), whose customers all buy in USD, so the figures here are in dollars. The other two group companies are quiet and add their own sales, so a group total moves by smaller percentages; read the story with `CompanyCode eq 'INA1'`.

"Why did sales drop in August 2026?" The data is built, with fixed arithmetic and no random numbers, so the correct answer is known. These figures are measured from the data and pinned by tests (`apps/butterfly/tests/test_story_ground_truth.py`).

| Factor | What the data says |
|--------|-------------------|
| The fall | July $94.7k, August $80.9k: $13.7k or 14.5% lower. Normal months are about $112k, and July is already 13.6% below June |
| Customer contract | Harborline Nutrition LLC (the biggest customer, about 12% of sales in July) has contract `0040000127`, valid to 2026-07-12, renewed only from 2026-09-14 by `0040000163`. Its orders stop on 12 July except a few small spot orders. Harborline: $11.3k in July, $0.3k in August, which is **$11.0k, 80% of the fall** |
| Supplier delay | Deccan Agro Growers Cooperative delivered Black pepper, whole on purchase order `4500001207` on 2026-07-26, promised 2026-07-14: 12 days late |
| Production delay | Production order `0001000417` for Piperine extract 95% (`RM-1002`) was planned 2026-07-06 to 2026-07-20 and finished 2026-08-03 (14 days late), reason `MATERIAL_SHORTAGE`, component Black pepper, whole |
| Effect on sales | From 2026-07-20 to 2026-08-31 the other customers order Piperine extract 95% about 40% less. Piperine sales to them: $9.4k in July, $4.2k in August, which is **$5.2k, 38% of the fall** |
| Offset | The other customers' remaining sales are about $2.5k higher in August than in July: **-18%** of the fall. A good answer reports it |
| Recovery | September is back to $99.9k and October to $113.6k |

The three parts are additive: Harborline 80% + pepper shortage 38% + offset (-18%) = 100%. They are not the same as "sales by customer" and "sales by material", which overlap (Harborline's lost orders include piperine).

Two decoys test that the agent does not blame everything it finds:

- Malnad Botanicals Pvt Ltd delivered Frankincense resin 4 days late in May (`4500001196`); Boswellia extract sales in May are normal.
- Production order `0001000408` for Probiotic capsule 10B CFU finished 6 days late in May for `MACHINE_BREAKDOWN`; probiotic capsule sales in May are normal.

Every other delivery is within 2 days of its promise and every other production order finished on time. As of 2026-10-31 next month's purchase orders are open and next month's production orders are running.

## 8. Phases

| Phase | What | Needs |
|-------|------|-------|
| butterfly 08 driver-data (done) | the contract, the entities and the first scenario | this document |
| synapse-api 07 summary-paging (done) | read every summary completely | butterfly 08 |
| butterfly 09 scenarios | the scenario switch and the other scenarios with their ground truth, two held back | butterfly 08 |
| butterfly 10 purchases | purchase value, purchase events and scenarios, so "why did purchases rise" is testable | butterfly 09 |
| synapse-api 08 compare (done) | compare two periods split by a dimension, volume against price, a month with its trend, for sales | butterfly 09 |
| synapse-api 09 metrics-records | a registry of metrics and record types; generic compare, month and records reads, so a new metric or record type is configuration | butterfly 09 |
| sami-agents 03 answer-questions | level 2: metric and period, sentence with figure, chart | synapse-api 08 |
| sami-agents 04 graph | `graph.toml`, loader, `graph check` and `graph show`, the traversal engine, the maintenance how-to | synapse-api 09 |
| sami-agents 05 analyst | question understanding, the three modes, ranking, validated answer, evaluation on the scenarios | sami-agents 03 and 04 |
| synapse-web 12 ai-answers | AI Mode shows text, chart and evidence | sami-agents 03 |
| SAP team | RAP views for the four entities (see the contract) | `docs/sap/drivers-contract.md` |

## 9. Risks

- **Correlation is not cause.** A contract that ended on the day a customer stopped ordering is a strong hint, not proof. The wording and the evidence list say so.
- **Data quality.** Delivery dates, production confirmations and contract validity in the real system may be incomplete or entered late. The agent reports what it cannot check.
- **The graph only knows what it is told.** A cause with no node or edge (a competitor, a quality complaint, a holiday) cannot be found; the answer then says nothing was found. Coverage grows by adding nodes and edges, and every addition is tested on a scenario.
- **Wrong or missing edges.** A wrong relationship gives a confident wrong path; `graph check` and the scenarios are the defence, and the answer always shows its evidence so a wrong path is visible.
- **Too many findings.** Every real month has late deliveries. Findings are ranked by the amount of the change they explain and anything below a small share is left out.
- **Performance.** A "why" question makes several calls; they run in parallel and use the 5-minute cache, and the answer has a time limit with a partial result.
- **Authorisation.** SAP sees one shared login for management users, so the app, not SAP, must keep a user to the data their role allows.
