# intent-api/01 scenario-rules

## Goal
A new backend app, `intent-api` (port 8006), that reads a manager's question and decides which approved scenarios it asks for. Laya (a small classification model, run as its own service) names the domain and picks among the scenarios of that domain; fixed rules own the scenario library, check that a scenario really exists and refuse everything else. The phase measures how well this does on a question set. Nothing is answered yet.

## Why
The first model-based attempt in sami-agents (one yes/no per scenario, 16 scenarios, 46 questions) gave the exactly right scenarios on 3 questions at 70% and 6 at 80%, with sales and purchases, and "why" and "compare", mixed up. A wrong answer is worse than "I cannot answer that yet". A first draft of this spec therefore used rules only. Tests of Laya on 2026-11-01 (`apps/intent-api/docs/laya/09-intent-api-notes.md`) changed that: when the question is a single choice among a few areas with short descriptions, a catch-all `Other` and the manager's text passed as `{"question": text}`, Laya put 59 of 65 business questions in the right area, spelling mistakes included, in about 0.55 seconds, and refused 13 of 16 questions that are not about the business. Longer descriptions, one yes/no per area and two layers of choices were all worse. The owner decided: Laya may choose, but only among options the app defines, and its choice is checked by rules; a refusal is never left to Laya alone.

## The whole path (each its own phase, this spec covers 01)
- 01 scenario-rules: app, scenario library, Laya gateway, domain and scenario selection, refusal rules, evaluation (this phase).
- 02 slots: periods ("last month", "Q3", "the last three months"), numbers ("top 5"), and customer, supplier and material names linked to the real names through synapse-api, typos included.
- 03 answers: a responder per scenario that fetches through synapse-api and builds blocks (text, trend, table, evidence) from templates; the `analyse` route; multi-part questions joined.
- 04 ai-mode: synapse-web asks intent-api; sami-agents is retired from AI Mode when the evaluation says intent-api is at least as good.
- Later: fine-tuning Laya on the owner's real questions if the evaluation shows it is needed, and Docker for the whole system (not before everything else is done).

## Behavior (this phase)
### The app
`apps/intent-api`, a `uv` workspace member with the folders of the constitution (`domain`, `application`, `infrastructure`, `entrypoint`), settings with `pydantic-settings`, the cookie check of the other APIs (`token-verification`), `GET /health`, and `POST /v1/intent/match`. Same conventions as sami-agents: routers and schemas under `infrastructure/api/<domain>/`. Scaffold is done (task 1).

### Laya as a separate service
Laya runs in its own process (`laya-serve`, own virtualenv, CPU torch; it runs on Python 3.14) and intent-api calls it over HTTP, configured by `LAYA_URL` and `LAYA_API_KEY`. Laya is behind a gateway (a port in `domain`, an HTTP adapter in `infrastructure`, a fake in the tests). If Laya is unreachable the answer is `problem: "cannot_classify_now"`, never a guess. Everything runs on the host for now; Docker comes at the very end.

### The scenario library (`apps/intent-api/scenarios.toml`, owner maintained)
The domains are Sales (exports and domestic: most sales go abroad, the USA first, in USD and INR; country, region and customer are dimensions, not a separate domain), Purchase (including imported raw materials, with the supplier's country), Shipments (dispatch, containers, in transit), Finance, Inventory and Production. Exports is not a domain. Each domain has a short `description` (three to six words, the words a manager uses) that is what Laya reads; Laya also gets an `Other: everything else` option.

Each scenario is a `[[scenario]]` table with: `id`, `domain`, `description` (short), `examples` (sample questions), `needs` (the slots it needs: `period`, `entity` (a customer or material for Sales, a supplier or material for Purchase; phase 02 resolves which), `top`), and `covers` (scenarios it makes redundant, for example "compare with previous" covers "value"). The loader rejects: a duplicate id, an unknown domain or slot, `covers` that loops or names an unknown scenario, a domain without a description, a scenario with no `examples`. A new scenario entry is all a new kind of question needs; the code knows no flow.

### The reader
1. Domain: one Laya choice question ("Which department should handle this?") over the domains and `Other`, state `{"question": text}`. The result keeps the probability of the chosen domain.
2. Refuse when Laya says `Other`, when the probability is below `DOMAIN_MIN_CONFIDENCE` (set from the evaluation), or when the domain has no scenarios yet. A refusal is `problem: "cannot_answer"` with the nearest domains as "did you mean" choices, and the question is appended to `unanswered.jsonl` (setting `UNANSWERED_LOG`).
3. Scenarios: the question is split into clauses at "and", commas, semicolons and "then"; for each clause one Laya choice question offers the scenarios of the chosen domain plus "nothing is asked", and the answers are joined. `covers` is applied afterwards and at most `MAX_SCENARIOS` (4) are kept, best first; a clause below `SCENARIO_MIN_PROBABILITY` counts as nothing. A named customer, supplier or material is not a scenario: it is the `entity` slot, found in phase 02, so "sales to X in August" selects the plain sales-figure scenario.
4. The response of `match` lists the domain, the selected scenarios, each with the probability Laya gave, and the options that were offered, so every decision can be read.

### Commands
- `intent-api scenarios check` and `scenarios show`, like `graph check` and `graph show` of sami-agents.
- `intent-api unanswered`: refusals grouped by nearest domain.
- `intent-api eval`: runs `evals/questions.json` (the question set in `reference/`: 34 answerable single and multi-part questions and 12 that must be refused, plus the questions added in this phase for the other domains, spelling mistakes and not-business questions, each with its expected domain and scenarios) against a running Laya and prints, for the chosen thresholds and for others: domain right, scenarios exactly right, a wrong or extra scenario, missing, correctly refused, wrongly refused, wrongly answered, and the time. Expected results are written before tuning, and a held-out part is not looked at until the end.

## Acceptance cases
- The library loader rejects each bad file in the list above with a clear message; `scenarios check` passes on the shipped file.
- With Laya running: "what were sales for August" and "why did purchases fall in May" select exactly their scenario; "how much do customers still owe us" selects a Finance scenario only if one exists, otherwise it is refused with Finance named.
- A question about weather, jokes, payroll or a forecast is refused with the nearest choices and one log line; spelling mistakes ("Augsut", "revnue") do not stop a question that is otherwise clear.
- Sales and purchases are never mixed in one answer.
- Laya down gives `cannot_classify_now`, not an error page and not a guess.
- The same question gives the same result every time Laya returns the same probabilities; the gateway never retries into a different answer.
- `test_no_outside_calls` lists only the Laya gateway; the tests run without Laya.
- `eval` reports the numbers above; the phase records them in `notes.md` with their limits and compares them with the first Laya test (3 and 6 exactly right of 34) before the phase closes.

## Out of scope
Slots (periods, numbers, names), fetching data, answers, fine-tuning Laya, any other model, the web app, retiring sami-agents, saving answers, Docker and any deployment files.

## Depends on
Nothing new in the repo (merged `token-verification`, `structured-logging`). A running Laya (`laya-serve`) outside the workspace; see `apps/intent-api/docs/laya/`. The owner supplies about 50 real manager questions; they are added to the evaluation as soon as they arrive and decide which scenarios are written first.

## Open items for the owner
1. The first scenarios to write beyond the 16 in `reference/scenarios.json` (needs the real questions).
2. Port 8006 and the name `intent-api` are assumed.
3. Is it acceptable that `unanswered.jsonl` keeps manager questions on the server's disk?
4. Which checkpoint: `typed-decisions` and `convaiinnovations/laya` tied at 59 of 65 on the domain question; the choice is made in task 2 on the larger set.
5. "profit margin" reads as Sales but belongs to Finance and has no scenario yet. Which domain should win?
