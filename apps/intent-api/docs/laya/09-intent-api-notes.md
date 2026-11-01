# What this means for intent-api

Our own tests (2026-11-01) and the conclusions we draw from the docs. Update this file whenever a test changes a conclusion.

## The idea
Laya classifies the manager's question in layers instead of rules matching words: first the root domain (sales, purchases, ...), then follow-up questions inside that domain (which period, is it a comparison, compare with what). Laya is expected to cope with spelling mistakes. The rest of the pipeline (slots, data, answers) stays deterministic. This reverses the "no model" decision of the first draft of phase 01; the spec and tasks need rewriting once the approach is chosen.

## Test setup
- In-process, no server and no API key: `laya.load(...)` from a separate Python 3.13 virtualenv with CPU torch. Python 3.14 (the workspace version) was checked afterwards and works too (see 03).
- 41 questions: the 34 in `specs/intent-api/01-scenario-rules/reference/queries.json` (expected domain from the first plan item's metric), 5 off-topic (weather, joke, cricket, capital of France, rainfall), 2 misspelled ("slaes for Augsut", "how much did we by in septembr").
- Scripts live in the session scratchpad, not in the repo. Move them into `apps/intent-api/evals/` when we keep them.

## Results

| Run | API | Labels | Right | Sales/purchases (34) | Off-topic refused (5) | Typos (2) | Median call |
|---|---|---|---|---|---|---|---|
| 1 | `system_one` + `criteria`, checkpoint `convaiinnovations/laya` | sales, purchase, customer, vendor, product, none | 24 of 41 | 20 | 5 of 5 (0.97 or more) | 0 | 346 ms |
| 2 | `decide()` + schema, optional enum | sales, purchases (+ null) | 35 of 41 (both checkpoints) | 34 | 0 of 5 (never used null) | 1 | 463 ms (laya), 513 ms (typed-decisions) |

Timings: 0.2 to 0.4 s for a one-sentence question, 0.5 to 0.9 s for multi-part questions, load about 5 s. A layered flow multiplies the per-call time by the number of layers asked sequentially (questions that do not depend on each other can go in one call).

Run 1 failures: purchases went to `none` ("how much did we buy", "top 5 suppliers by spend", "what did we spend with Doosan", "how come procurement fell in may" at 0.97); customer/product labels overlapped with sales; typo "septembr" went to sales.
Run 2 failures: all five off-topic questions got a domain at confidence 0.50 to 0.57 (essentially the two-option floor); "how much did we by in septembr" went to sales at 0.94 (laya) or 0.79 (typed-decisions), a confident wrong answer.

Run 2's wording that fixed purchases: "Is the manager asking about sales (money received from customers: sales, revenue, turnover, invoiced, sold) or about purchases (money spent with vendors and suppliers: purchases, buying, bought, spend, spending, procurement)?"

## Corrections to our own first reading of the docs
- `system_one` with `instructions` + `criteria` is a documented, supported form (the use-cases page uses it throughout). It was not the mistake; `decide()` is the typed convenience over the same engine. What changed run 1 to run 2 was most likely the explicit question text with synonyms, and dropping the broad `none` label, but we did not isolate which. Run each factor alone before concluding.
- The null branch in `decide()` is not an abstain signal by itself; in our test the model never chose it.

## What the docs imply for us
1. **Confidence needs a gate, but the shipped one is not trustworthy.** Gate on `answer_confidence` / `min_confidence`; thresholds must be fitted on our own held-out questions (05). A fixed 0.9 would not have caught the confident wrong "septembr" answer, and a 0.6 floor would refuse real purchase questions (lowest real was 0.52 to 0.55).
2. **Refusal should be its own decision.** Docs patterns for gateways and firewalls use a separate `noul` ("is this about our business figures?") and a `complex`/`none` escape route. Run 1 showed an explicit `none` label can refuse off-topic questions very well, but it also swallows real questions when its description is broad. Try: sales / purchases / other with a narrow "other" description, plus a separate `noul`, and measure both. Keep the refusal threshold from data.
3. **Keep options few.** About 20 is the documented ceiling; we have 2 to 6 at each layer, which is comfortable. Layers (domain, then compare-or-not, then compare-with-what) also keep each question's options small.
4. **Order and wording matter.** Test alternate label orders and rephrased descriptions (05, Wording and order), and negated questions ("not including"), since the docs list confident failures there.
5. **Do not rely on Laya for spelling.** Results were mixed (1 of 2 typos). Options: a small typo-normalisation step in front (the original spec had `difflib`), or accept refusal and log. The owner chose to rely on Laya; keep a typo set in the evaluation so the decision stays measured.
6. **Reduce confident-wrong risk beyond a threshold.** Candidates from the docs: `OptionStabilityHook` (stability across reordered or renamed options, about 2x to 3.7x CPU cost, 04), asking a second differently worded question and requiring agreement, and the deterministic checks that follow (a scenario that needs a supplier name cannot proceed without one). Not yet tried.
7. **Fine-tuning is the documented fallback.** If zero-shot stays at about 90% on our domains, a fine-tune on a few hundred labelled manager questions is the supported way up (07). It needs those questions; the owner's ~50 real questions are the start.
8. **Deployment shape.** Laya runs on Python 3.14 with CPU torch (checked), so it could be loaded inside intent-api or run as its own process (`laya-serve`) that intent-api calls over HTTP like sami-agents already does. In-process puts about 1 GB of torch and a 6 s load in the API; a separate process keeps the API light and restartable (`apps/sami-agents/.../laya_case_model.py`). Set `LAYA_API_KEY` for any non-local use; on this machine the server on port 8000 belongs to an earlier session. One worker, one forward pass at a time: concurrency is serial, which matters if layered calls multiply.
9. **Staged rollout.** Shadow-log Laya next to the rules matcher, compare, then promote (07). The evaluation set, held-out part and "expected results written before tuning" rules in the spec still apply.

## Run 3: refusal (2026-11-01)
Set: 38 in-scope (34 queries.json + 4 typos) and 20 out-of-scope (weather, jokes, forecast, inventory, payroll, production, greetings, nonsense, "profit margin", "stock level of steel coil"). `decide()` with two designs, both checkpoints.

| Checkpoint | Design | In-scope right | Wrongly refused | Off-topic refused | Median call |
|---|---|---|---|---|---|
| laya | A: enum sales / purchases / other (narrow "other") | 31/38 | 5 | 17/20 | 554 ms |
| laya | B: enum sales / purchases + boolean in_scope | 25/38 | 12 | 17/20 | 780 ms |
| typed-decisions | A | 29/38 | 7 | 18/20 | 571 ms |
| typed-decisions | B | 22/38 | 15 | 17/20 | 777 ms |

Findings:
- Design A (a third "other" option) beats the separate boolean gate. The boolean said "not in scope" for ordinary questions ("sales in june, july and august", "why did sales drop") at 0.5 to 0.95, and approved "stock level of steel coil" and "predict our sales for next year". Drop design B.
- Neither design reaches usable refusal AND acceptance together. Remaining errors fall in three groups: misspelled words (slaes, revnue, purchse, qarter: 4 of 7 laya misses), purchases wording without the word "purchases" ("how come procurement fell"), and near-business topics (forecast of sales, profit margin, stock level) that Laya reads as sales or purchases.
- Confidence does not separate the groups cleanly: wrong answers sit at 0.38 to 0.85 and right ones at 0.52 to 0.98, so one threshold cannot fix it.
- Run 2 (two-way, no refusal) got all 34 real questions right. Run 3 A trades some of those for refusal: the "other" option pulls in real purchases questions.
- Out-of-scope questions that look like our topics (forecast, margin, stock) are not a classification problem alone. They need a scenario list: "is there an approved scenario for this?" is answered by the second layer, not the domain layer.

Implication: Laya as the first layer is good at sales versus purchases for clearly worded questions and fast enough, but it will not be the only refusal mechanism. Likely design: Laya proposes the domain; the deterministic layer checks that a scenario exists and its needs are met; refusal stays a rule, not Laya's "other".

## Run 4: all app domains at once (2026-11-01)
One `system_one` choice question over the six widget categories of the app (Sales, Purchase, Finance, Inventory, Exports, Production; Sales is in `sales_widgets.py`, the others in `mock_library.json`), each option with a short description built from its widgets, optionally plus `none`. 67 questions: 38 sales/purchases, 17 across Finance, Inventory, Exports and Production (written by us), 12 not about the business.

| Checkpoint | Options | Right (of 67) | In-domain right (of 55) | Not-business refused (of 12) |
|---|---|---|---|---|
| laya | 6 domains | 40 | 40 | 0 (no option) |
| laya | 6 domains + none | 33 | 22 | 11 |
| typed-decisions | 6 domains | 46 | 46 | 0 |
| typed-decisions | 6 domains + none | 48 | 37 | 11 |

Findings:
- Presenting all domains is clearly worse than the two-way sales/purchases question (34 of 34 on the real questions). Purchase questions drift to Sales and Finance; Exports ("export revenue", "shipments in transit") lands in Sales; Production ("scrap", "output against plan") lands in Sales.
- Probabilities spread over six options: the correct answer is often only 0.3 to 0.5, so confidence thresholds have even less room.
- With `none` added, `laya` sends most real questions to `none` (22 of 55 in-domain right); `typed-decisions` is less affected (37 of 55). The `none` label pulls like before.
- `typed-decisions` is better than `laya` here; it was only equal in runs 2 and 3. Checkpoint choice needs its own comparison.
- Uncontrolled: the option descriptions here differ from runs 1 to 3, so we cannot tell how much is the number of options and how much the descriptions. Next controlled test: same descriptions, vary the number of options (2, 3, 4, 6).
- Hierarchy is the documented direction anyway: asking a narrow question first (is it money in or money out, is it stock or production) keeps each question to 2 to 3 options.

## Run 5: three ways to ask (2026-11-01)
Same 67 questions and the same six option descriptions as run 4 (55 about the business, 12 not). Layered = first a choice among selling (Sales, Exports) / buying (Purchase) / money (Finance) / operations (Inventory, Production), then a second choice inside the group. Yes/no = six `noul` questions in one call, highest wins if at least 0.5, otherwise none.

| Checkpoint | Design | Business right (of 55) | Non-business refused (of 12) | Median call |
|---|---|---|---|---|
| laya | six-way choice | 40 | 0 (no option) | 869 ms |
| laya | layered choices | 35 | 0 (no option) | 1108 ms |
| laya | six yes/no, one call | 35 | 11 | 2088 ms |
| typed-decisions | six-way choice | 46 | 0 (no option) | 810 ms |
| typed-decisions | layered choices | 44 | 0 (no option) | 1148 ms |
| typed-decisions | six yes/no, one call | 29 | 12 | 1781 ms |

Findings:
- Layering did not help: the first layer already confuses buying with selling, so the second layer inherits the mistake. It adds a call (about 1.1 s).
- Yes/no per domain refuses non-business questions best (11 and 12 of 12, top confidence about 0.12 to 0.21) but misses many business questions ("sales to Acme in August" scored below 0.5 on every domain). Six yes/no questions take 1.8 to 2.1 s, slower than one choice.
- Purchases is the persistent weak domain in every design (4 to 10 wrong of about 12), usually read as Sales or Finance.
- typed-decisions beats laya on the choice designs; laya is better on yes/no.
- The 0.5 cut for yes/no was not tuned: lowering it and requiring a margin over the runner-up could recover the missed business questions. Not tested.
- Best single result so far for picking a domain remains the two-way sales/purchases choice (34 of 34); beyond that, nothing in this family is reliable enough to act on without rules or fine-tuning.

## Run 6: what we were missing (2026-11-01) - supersedes the pessimistic conclusions of runs 3 to 5
The owner had seen Laya classify well. The README guidance (short descriptions per label, a catch-all `other`, a direct question, state as text or a dict with named fields, about 192 to 256 head tokens shared by all options) differed from our setup in three ways. Token budget was checked and was not the cause (150 of 256 head tokens used, nothing truncated). One factor changed at a time, six-way choice, 55 business questions:

| Variant | typed-decisions | laya |
|---|---|---|
| A long keyword-list descriptions (runs 4 and 5) | 46 | 40 |
| B short descriptions ("sales orders, revenue, customers") | 49 | 48 |
| C B + question "Which department should handle this?" | 49 | 50 |
| D C + state as a dict `{"question": q}` | **52** | **52** |
| E labels only, no descriptions | 45 | 44 |
| F lowercase labels + short descriptions | 49 | 50 |

- Short descriptions were the largest single gain; a dict state with a named field added another 2 to 3.
- With D plus an `Other: everything else` option: business 50/55, non-business refused 9/12 on both checkpoints. The three non-refused: payroll, "poem about steel", "25 times 17" (steel and arithmetic drift to Production).
- Remaining business misses with D: the typo "by in septembr" (Purchase read as Sales at 0.83 to 1.00), "profit margin" (Finance read as Sales; no finance margin widget exists), and "export revenue last month" (Exports read as Sales; arguably ambiguous because both words are sales words).
- Take-away: our earlier conclusions about layering, yes/no and "all domains is worse" were drawn with the long-description setup; they should be repeated with variant D before being believed. The recommended form now is one choice with short descriptions, a named-field dict state and an `Other` option, fine-tuned or gated afterwards.

Recommended Laya call shape (current best):
```python
state = {"question": text}
questions = {"department": {"type": "choice", "instructions": "Which department should handle this?",
  "criteria": {"Sales": "sales orders, revenue, customers", "Purchase": "purchases, spend, suppliers, vendors",
               "Finance": "receivables, payments, overdue, cash", "Inventory": "stock, warehouses, reorder",
               "Exports": "export shipments, destinations", "Production": "production, machines, scrap, output",
               "Other": "everything else"}}}
```

## Run 7: three designs again with the Run 6 setup (2026-11-01)
Short descriptions, `{"question": q}` state, question "Which department should handle this?", catch-all `Other`. 81 questions: 65 business (the 55 + 8 typos + 2 multi-domain) and 16 not about the business. Layered = Selling (Sales, Exports) / Buying / Money / Plant (Inventory, Production) / Other, then a second choice. Yes/no = six `noul` in one call, best at 0.5 or more else Other.

| Checkpoint | Design | Business right (of 65) | Non-business refused (of 16) | Median call | Confidence right (median / p10) | Confidence wrong (median) |
|---|---|---|---|---|---|---|
| typed-decisions | six-way + Other | **59** | 13 | 590 ms | 0.81 / 0.48 | 0.49 |
| typed-decisions | layered + Other | 53 | 15 | 824 ms | 0.52 / 0.32 | 0.36 |
| typed-decisions | six yes/no | 34 | 16 | 1745 ms | 0.63 / 0.52 | 0.47 |
| laya | six-way + Other | **59** | 13 | 541 ms | 0.99 / 0.66 | 0.57 |
| laya | layered + Other | 51 | 12 | 834 ms | 0.72 / 0.40 | 0.35 |
| laya | six yes/no | 34 | 16 | 1579 ms | 0.77 / 0.55 | 0.39 |

Findings:
- One six-way choice with short descriptions and `Other` is the best design: 59 of 65 (91%) on both checkpoints, about 0.55 to 0.6 s, one call. Layering costs 0.25 s more and loses 6 to 8 questions. Six yes/no loses half the business questions (real sales questions score 0.2 to 0.5 on "is this about sales"), so the yes/no form is not usable at a 0.5 floor.
- Typos in the 8 added typo questions were handled: only "overdu accounts" was missed (on both checkpoints), plus the earlier "by in septembr" (Purchase read as Sales at 0.82 to 1.00, a confident wrong answer).
- Remaining six-way misses (typed-decisions): "how come procurement fell in may" and "output against plan today" go to Other at about 0.42; "profit margin" and "export revenue" go to Sales; "by in septembr" and "overdu accounts" are typos.
- Confidence is more useful than before: with laya the right answers sit at median 0.99 and p10 0.66 while the wrong ones have median 0.57. A floor around 0.6 to 0.65 would catch most misses but also refuse some right answers (and not the confident Sales misreads). Pick from the larger evaluation set, not these 81.
- Non-business refusal is 13 of 16 with `Other`; adding scenario existence checks after the domain (rules) covers the rest.

## Next tests (not yet run)
- Refusal alone: sales / purchases / other with narrow descriptions, plus the `noul` gate, on a larger off-topic and out-of-scope set (forecasts, weather, jokes, other departments, empty and gibberish input).
- Isolate wording versus label set versus API form.
- Both checkpoints (`convaiinnovations/laya`, `typed-decisions`) on each of the above.
- More typo cases (10 to 20) and negation cases.
- Second layer: comparison-or-not and compare-with-what on the multi-part questions; measure total latency for 2 and 3 layers (and whether independent questions can share one call).
- Fit a threshold on a calibration slice and report ECE and selective accuracy.
