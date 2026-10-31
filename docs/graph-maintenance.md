# Maintaining the graph

`apps/sami-agents/graph.toml` says what relates to what and what counts as unusual. The code that walks it knows nothing about sales, suppliers or production: add a line here and the next question can use it. You change this file, not code, unless you need a new *kind* of anomaly.

## The ideas
- A **node** is a kind of thing whose rows can be read: a record type from synapse-api (`record:contract`) or a member of a split from a metric (`metric:sales.customer`, a customer or a material).
- An **edge** says one node can cause another: `cause`, `effect`, the field that ties them (`join`), which anomalies of the cause it passes on (`carries`), which anomalies it shows at the effect (`shows`) and how far back to look (`lookback_days`, default 60).
- An **anomaly** says when a node's rows are unusual. There are four kinds:

| Kind | Use it when | Parameters |
|------|-------------|------------|
| `later_than` | a date should not be later than another (delivery, production end) | `due`, `done`, `min_days` (default 3), optional `reason` (a field that says why, kept as evidence) |
| `coverage_gap` | rows give validity periods and a gap matters (contracts, price lists) | `from`, `to` |
| `sum_changed` | a quantity added up over the period moved a lot (planned quantity, ordered quantity) | `field`, `date`, `min_percent`, `pad_days` (default 30) |
| `value_changed` | a member of a metric split moved a lot (a customer's sales, a material's purchases) | `min_percent` |
| `set_changed` | the set of values of a field changed between periods: a new or a vanished supplier or customer | `field`, `date`, `pad_days` (default 30) |

- A record node may name an `id` field (`id = "PurchaseOrder"`): the field that identifies one row, so an answer can say which document it found.
- A **passthrough** node is a link that is walked through without a test, such as the list of components of a production order.

Going back from an effect (root cause), an edge that lists `shows` is only followed when the kind found at that effect is one of them, so a change of supplier is not "explained" by production plans. A starting mover has no kind and follows every edge.

Supply delay and extra demand travel opposite ways through the same nodes, so a pair of nodes can have two edges, one each way, carrying different kinds. Look at the existing ones with `sami-agents graph show`.

## Adding a node and an edge
Say purchase prices can only move when a price list has a gap, and a record type `price_list` is already in `apps/synapse-api/registry.toml`.

1. Make sure the record type exists in the registry and its entity is in a contract under `docs/sap/`. If not, that is the first change (a registry entry, the contract, then butterfly or the SAP view).
2. Add the node:

```toml
[node.PriceList]
source = "record:price_list"
anomaly = { kind = "coverage_gap", from = "ValidFrom", to = "ValidTo" }
```

3. Add the edge that connects it. The `join` fields are the ones that hold the same value on both sides; on a record they must be among that record type's `key_fields` in the registry, on a metric node the field is always `key`:

```toml
[edge.price_lists_of_material]
cause = "PriceList"
effect = "PurchasedMaterial"
join = { cause = "Material", effect = "key" }
carries = ["coverage_gap"]
```

4. Run `uv run --package sami-agents sami-agents graph check`. It tells you, by name, about a source that is not in the registry, a field the contract does not list, a join field that is not a key field, a kind that the node does not define, a wrong parameter, and nodes that nothing connects. Fix what it says until it prints `ok`. Lines starting with `info:` are loops, which are allowed (a walk stops at its limits).
5. Run `uv run --package sami-agents sami-agents graph show` (add `--mermaid` for a diagram) and read the result as a sentence: "a gap in the price list can cause a change in purchases of the material".
6. Add a scenario to butterfly (or a real past case) with the expected cause, and check the walk finds it. Add a case where the thing is present but did *not* matter: a good graph reports nothing there.

## Rules of thumb
- Prefer many small edges over one clever one. Each edge should read as a plain sentence.
- A threshold (`min_days`, `min_percent`) is a judgement. Start loose, look at what is reported on cases you know, and tighten it. Write the reason beside the entry in a TOML comment.
- Never put a name, a customer or a date in the file. The file describes kinds of things; the question supplies the rest.
- A walk only reports things the data holds. If nothing is reported, the right answer is "nothing found in the data we hold", not a stretch.
- Walks stop at depth 6, 100 lookups or 200 calls and say so (`truncated`). If you need more depth, the graph is probably too fine-grained.

## Limits to know
- `sum_changed` and `value_changed` carry no date, so the check that a cause comes before its effect only applies between `later_than` and `coverage_gap`.
- A member of a metric split is found among the top 50 changes of its dimension; a smaller mover is not seen.
- Several rows of a node reached by one step are judged together for `sum_changed` (all orders that use one material), but one by one for `later_than`.
