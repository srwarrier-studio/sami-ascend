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

## Run 8: company-shaped domains (2026-11-01)
After the owner described the business (mostly exports, USD and INR, raw material imports), the domains became Sales (exports and domestic together), Purchase (including imports), Shipments, Finance, Inventory, Production, with short descriptions in `apps/intent-api/scenarios.toml`. Check through the real app code (`ReadDomain` + `LayaChoiceClassifier`, `typed-decisions`): 40 invented questions in this shape (export sales by country and in USD, imported turmeric, shipments in transit, overdue export receivables, extraction plant scrap, plus 6 not about the business).
- 39 of 40 right, median 364 ms per call. The one miss: "slow moving raw materials" read as `Other` (0.26) instead of Inventory.
- "export revenue last month" now lands in Sales, the ambiguity of run 4 is gone with the merged domain.
- Questions and names are invented (Lakeview Botanicals, Kaveri Growers, Medan Agro Traders); no real company data was used or shared. The reference question files in the spec folder were changed to these names.
- Small and friendly set written by us: it says the descriptions work, not how real managers will phrase things. The evaluation task must keep a held-out part and take in the owner's real questions through a local run.

## Run 9: scenarios inside a domain (2026-11-01)
The domain is given (from the reference answers); the question is which of the domain's scenarios are asked. `typed-decisions`, reference questions that stay inside one domain (33 of 34; the one that mixes sales and purchases is out because a question is answered in one domain), 14 to 16 scenarios, expected sets with `covers` applied.

| Design | Exact (of 33) | Median call |
|---|---|---|
| one yes/no per scenario, cut 0.3 | 2 | 2.8 s |
| one yes/no per scenario, cut 0.5 | 9 | 2.5 s |
| one choice over the whole question | 17 | 0.75 s |
| + one example per option | 16 | 1.3 s |
| iterative choice with a stop option | 8 to 12 | 2.3 to 3.0 s |
| one choice per clause (split at and, commas, then) + "nothing" option | 23 | 1.1 s |
| same, `entity_value` scenarios dropped (entity becomes a slot) | **27** | 0.8 s |
| same, richer words in the descriptions | 26 | 1.3 s |
| same on `convaiinnovations/laya` | 24 to 25 | 0.9 s |

Through the real app code (`ChooseScenarios`, 14 scenarios): 27 of 33 exact (82%), median 995 ms. Probabilities help: the lowest probability among the selected scenarios is a median of 0.64 for right answers and 0.39 for wrong ones, so a floor of about 0.5 would catch most misses (to be set by the evaluation).

Findings:
- Yes/no per scenario is clearly the wrong design again; clauses plus one choice each is the best so far.
- Whether a customer, supplier or material is named is not something Laya decides well (5 of the 10 misses in the first clause run); it belongs to name matching in phase 02, so the two `*_entity_value` scenarios were removed from the library and the plain value scenarios mention it in their description.
- Remaining misses are about comparison words ("versus the month before", "up or down against") read as plain value or trend, "revenue by customer" read as value, and one compare-with-last-year mix-up.
- 82% on questions we wrote ourselves is under the 90% bar floated for the evaluation; this is the step where fine-tuning would help most.

## Run 10: the whole pipeline on the evaluation set (2026-11-01)
`intent-api eval` on the 79 tuning questions of `apps/intent-api/evals/questions.json` (113 in all; 34 held out and not looked at yet; 50 answerable, 29 that must be refused: other domains without scenarios, forecasts, not-business). Real Laya, 1.3 s per question (domain call plus one call per clause).

Without any floor (`typed-decisions`): exact 36 of 50 answerable, wrong or extra scenario 10, missing 3, wrongly refused 1; refused correctly 24 of 29, wrongly answered 5; domain right 72 of 79; harmful (wrong or extra + wrongly answered) 15.

The trade-off, `typed-decisions` (domain floor / scenario floor: exact, harmful, wrongly refused):
| Floors | Exact | Harmful | Wrongly refused | Correctly refused |
|---|---|---|---|---|
| 0 / 0 | 36 | 15 | 1 | 24 |
| 0 / 0.3 | 36 | 11 | 1 | 26 |
| 0 / 0.4 | 30 | 7 | 7 | 28 |
| 0.4 / 0.4 | 29 | 5 | 10 | 28 |
| 0.5 / 0.4 | 23 | 4 | 16 | 29 |
| 0.6 / 0.6 | 13 | 0 | 30 | 29 |
`english` (`convaiinnovations/laya`) is worse: 32 exact, 15 harmful at no floor, and its probabilities are so flat that floors barely help (0.5 / 0.5: 27 exact, 5 harmful).

Reading:
- No setting gives both "answers most things" and "never gives a wrong answer". Zero harmful needs floors of about 0.6, which refuses 30 of the 50 answerable questions. Around 0 / 0.4 it answers 30 exactly right, 7 wrong or extra, refuses 7 answerable and 1 out of 29 must-refuse questions is answered.
- Harmful cases at no floor are of three kinds: forecasts and margins that look like sales questions (`predict export sales` answered as `sales_value` at 0.29 to 0.33), comparison wording read as value or trend ("up or down against last month", "relative to April"), and a few confident domain slips ("which buyers took the most from us" read as Purchase 0.79).
- A floor of 0.3 on scenarios removes the forecast cases cheaply (harmful 15 to 11 with no extra refusals); beyond that every step costs correct answers.
- Zero-shot, on questions written by us, does not yet meet an "at least 90% exact and no wrong answers" bar. That is the point where the owner's real questions and fine-tuning (docs/laya/07) come in.

## Run 11: held-out questions with the chosen floors (2026-11-01)
Floors chosen with the owner (their go-ahead on the recommendation): `DOMAIN_MIN_PROBABILITY` 0, `SCENARIO_MIN_PROBABILITY` 0.3. The 34 held-out questions were run once, with `--final`, after the floors were fixed on the tuning questions (`typed-decisions`).
- Answerable (24): exact 19 (79%), wrong or extra scenario 4, missing 0, wrongly refused 1.
- Must refuse (10): correctly refused 9, wrongly answered 1.
- Domain right on 33 of 34. Harmful (wrong or extra + wrongly answered): 5 of 34 (15%).
- The misses: "are export sales higher than a year ago" read as trend; "compare imports this month with last month" read as compare-with-last-year; "top suppliers this quarter" read as Sales (top customers) at domain 0.33; "sles for last mnth" read as compare-with-last-year; "what will curcumin sales be next quarter" answered as a plain sales figure at 0.50 (a forecast); "which products brought the most revenue this year" refused.
- Tuning questions at the same floors: exact 36 of 50, harmful 11 of 79. Held-out is not worse than tuning, so the floors did not overfit; both say the same: about four in five answerable questions come out exactly right and about one in seven questions gets a wrong answer where a refusal was right.
- This held-out set is now spent for threshold choices; a new one is needed before the floors are changed again.

## Run 12: the spend question and the domain floor (2026-11-01, phase 02 task 1)
A manager's real try in AI Mode: "how much did we spend in october 2025?" was read as Sales at 0.26 (Purchase 0.22, Other 0.18), answered with `sales_value`. Adding "money we earn" and "money we pay out" to the domain descriptions did not help (0.31), so wording alone is not the fix. Six spend and earn questions and two questions taken from the SAP article ("which suppliers have had late deliveries this month", "what was our highest-margin product last quarter") were added to the tuning questions (87 now; held-out untouched). `typed-decisions`, scenario floor 0.3:

| Domain floor | Exact (of 56 answerable) | Wrong or extra | Wrongly refused | Must refuse, correct | Harmful (wrong or extra + wrongly answered) |
|---|---|---|---|---|---|
| 0 | 41 | 9 | 1 | 27 of 31 | 13 |
| 0.4 | 37 | 5 | 9 | 27 of 31 | 9 |

At 0.4 the generic spend questions (0.25 to 0.34) are refused as `not_sure` with Sales and Purchase suggested, four fewer wrong answers for four more exact answers lost. "Highest-margin product last quarter" is still answered as `sales_top_materials` (domain 0.40, scenario 0.31), the margin question the owner assigned to Finance (no scenario). `DOMAIN_MIN_PROBABILITY` default is now 0.4; the demo in AI Mode runs with it.

## The SAP article (read 2026-11-01, `docs/sap-genai.html`, "How GenAI can make ERP insights more accessible", Timo Elliott, 21 July 2025)
Relevant points: small language models fine-tuned on the company's own data, with retrieval, so users ask in natural language instead of dashboards (our direction, with Laya as the small model); ERP data is tables with relationships, so knowledge graphs help (sami-agents `graph.toml` is that idea); a toolset needs grounding, data masking, prompt management and lifecycle management (our answers will be grounded in synapse-api, data stays local); start by mapping what the ERP covers (our domains), train users and let them practise in low-risk settings (the "Reading preview" card). Its example questions, "highest-margin product last quarter" and "which suppliers have had late deliveries this month", are the kind of question we do not have scenarios for yet and are in the tuning set as must-refuse questions.

## Run 13: the fine-tuned checkpoint (2026-11-01, phase 02 task 4)
Trained by the owner on a remote GPU (`Training/intent-training.ipynb`): base `typed-decisions`, 1,862 training items (206 held out by Laya for calibration), 10 epochs, soft cross-entropy, options shuffled. The training loss was about 0 from epoch 3. Notebook table on the 921 held-out family items: accuracy 0.767 to 0.953, ECE 0.170 to 0.040, mean confidence 0.597 to 0.993. The calibration slice came from the training families (accuracy 1.0, temperature 0.998), so confidence is not corrected for unseen wording.

Served on the host as an extra checkpoint (`LAYA_EXTRA_MODELS={"intent-tuned": "<folder>"}`, `LAYA_MODELS=intent-tuned`, `LAYA_MODEL=intent-tuned`), then `intent-api eval` (floors 0.4 / 0.3):

| | Zero-shot `typed-decisions` | Tuned |
|---|---|---|
| Tuning questions (87): exact of 56 answerable | 37 | 51 |
| Wrong or extra scenario | 5 | 2 |
| Wrongly refused | 9 | 2 |
| Must refuse, correct (of 31) | 27 | 29 |
| Harmful (wrong or extra + wrongly answered) | 9 | 4 |
| Held-out questions (34): exact of 24 | 19 (at 0 / 0.3) | 23 |
| Held-out harmful | 5 | 0 |
| Seconds per question | 1.2 to 1.3 | 1.2 |

Remaining tuning failures: "is turnover up or down against the previous month" and "how much did we invoice customers in June" read as Finance (0.95 and 0.99), "what was spending in december last year" given compare-with-last-year, two multi-part questions with a wrong or missing second scenario, and two must-refuse questions answered ("slow moving raw materials" as purchases_top_materials, "which suppliers have had late deliveries this month" as top suppliers).

Fresh probes written after training, with phrasing not in the families (24): 22 right; the two misses were "which vendor gets most of our money" (Sales, 0.72) and "what was the best month for sales this year" (refused; no such scenario, so the refusal is defensible).

Limits:
- Confidence is now about 1.0 for nearly everything, so the floors (`DOMAIN_MIN_PROBABILITY`, `SCENARIO_MIN_PROBABILITY`) no longer separate right from wrong; the sweep is flat. Refusals now come from `Other`, a domain without scenarios and "nothing is asked", all learned. Confident mistakes (domain 0.95 to 1.00) are the remaining risk.
- The evaluation questions and the training families have the same author, and only exact repeats were removed, so these numbers measure our style. The owner's local set of real-sounding questions is the honest test; only totals are to be shared.
- The held-out evaluation questions were already used once for the floors in phase 01, so they are a sanity check, not a clean test.
- The checkpoint is large (840 MB model, 1.5 GB zip) and is not committed; it lives in `Training/intent-tuned/` (git-ignored) next to the zip.
- The training warning "Conflicting schema detected for question 'choice'" came from the domain and scenario items sharing one question id; it did not stop training or change the results above.

## Next tests (not yet run)
- Refusal alone: sales / purchases / other with narrow descriptions, plus the `noul` gate, on a larger off-topic and out-of-scope set (forecasts, weather, jokes, other departments, empty and gibberish input).
- Isolate wording versus label set versus API form.
- Both checkpoints (`convaiinnovations/laya`, `typed-decisions`) on each of the above.
- More typo cases (10 to 20) and negation cases.
- Second layer: comparison-or-not and compare-with-what on the multi-part questions; measure total latency for 2 and 3 layers (and whether independent questions can share one call).
- Fit a threshold on a calibration slice and report ECE and selective accuracy.
