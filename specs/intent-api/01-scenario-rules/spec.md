# intent-api/01 scenario-rules

## Goal
A new backend app, `intent-api` (port 8006), that reads a manager's question and decides which approved scenarios it asks for, using fixed rules only, and measures how well it does on a question set. No model of any kind is called in this phase. Nothing is answered yet.

## Why
The model-based readers in sami-agents are not reliable enough to put in front of management: a first Laya test (one yes/no per scenario over 16 scenarios, 46 questions) gave the exactly right scenarios on 3 questions at 70% and 6 at 80%, with sales and purchases, and "why" and "compare", mixed up (`reference/` holds the question set, `notes.md` of this phase the numbers). A wrong answer is worse than "I cannot answer that yet". The owner decided: a deterministic service that owns the scenario library and builds its answers from templates and data; a model may help later only to choose among candidates the rules already found, never to widen them, and only if it measures better than the rules alone. The service is built in small phases the owner takes part in.

## The whole path (each its own phase, this spec covers 01)
- 01 scenario-rules: app, scenario library, rule matcher, evaluation (this phase).
- 02 slots: periods ("last month", "Q3", "the last three months"), numbers ("top 5"), and customer, supplier and material names linked to the real names through synapse-api, typos included.
- 03 answers: a responder per scenario that fetches through synapse-api and builds blocks (text, trend, table, evidence) from templates; the `analyse` route; multi-part questions joined; the existing figure and why answers move in (the why answer calls sami-agents `analyse` over HTTP until it is ported).
- 04 laya-assist: Laya (choice questions) only to pick among candidates the rules found when they are close, kept only if the evaluation shows it better than rules alone.
- 05 ai-mode: synapse-web asks intent-api; sami-agents is retired from AI Mode when the evaluation says intent-api is at least as good.

## Behavior (this phase)
### The app
`apps/intent-api`, a `uv` workspace member with the folders of the constitution (`domain`, `application`, `infrastructure`, `entrypoint`), settings with `pydantic-settings`, the cookie check of the other APIs (`token-verification`), `GET /health`, and `POST /v1/intent/match`. Same conventions as sami-agents: routers and schemas under `infrastructure/api/<domain>/`.

### The scenario library (`apps/intent-api/scenarios.toml`, owner maintained)
Each scenario has: `id`, `category` (sales, purchases), `description`, `examples` (sample questions), `words` (the words and phrases that point to it, with synonyms: `why`, `reason`, `how come`; `compare`, `versus`, `against`; `top`, `largest`, `biggest`, `best`), `needs` (the slots it needs: `period`, `entity` of a type, `top`), and `covers` (scenarios it makes redundant, for example "compare with previous" covers "value"). The loader rejects: a duplicate id, an unknown category or slot, `covers` that loops or names an unknown scenario, a scenario with no `words` or no `examples`. A new metric or dimension in the registry plus a scenario entry is all a new kind of question needs; the code knows no flow.

### The matcher (rules, no model)
1. Normalise the question: lower case, punctuation, a few contractions, simple stemming (the same idea as sami-agents `keyword_matcher`, copied and kept small, not imported from another app).
2. Typos: words of 5 letters or more are matched to known words with `difflib` (cutoff 0.8).
3. Category: metric words (`sales`, `revenue`, `bought`, `spend`; the lists live in the library file, not in code) choose sales, purchases or both; none found means no category and no scenario.
4. Score each scenario of the category: how many of its `words` are in the question, with longer phrases weighing more, minus conflicting words (a `why` question does not match "value").
5. Select every scenario at or above `MATCH_MIN_SCORE` (default set from the evaluation), apply `covers`, keep at most `MAX_SCENARIOS` (4).
6. Nothing selected: `problem: "cannot_answer"`, the two nearest scenarios as "did you mean" choices, and the question appended to `unanswered.jsonl` (a local file, setting `UNANSWERED_LOG`).
The response of `match` lists the selected scenarios with their score and the words that matched (`why_matched`), so every decision can be read.

### Commands
- `intent-api scenarios check` and `scenarios show`, like `graph check` and `graph show` of sami-agents.
- `intent-api unanswered`: refusals grouped by nearest scenario.
- `intent-api eval`: runs `evals/questions.json` (the question set in `reference/`: 34 answerable single and multi-part questions and 12 that must be refused, each with its expected scenarios) and prints, for the chosen threshold and for others: exactly right, a wrong or extra scenario, missing, correctly refused, wrongly answered. Expected results are written before tuning, and a held-out part is not looked at until the end.

## Acceptance cases
- The library loader rejects each bad file in the list above with a clear message; `scenarios check` passes on the shipped file.
- A single question ("what were sales for August", "why did purchases fall in May") selects exactly its scenario.
- "I need sales of August compared to the last three months and the largest customer in the period" selects the comparison and the top-customer scenario, not the plain value one.
- A typo ("Augsut", "revnue") still matches; a question about weather, jokes or forecasts selects nothing and is refused with two choices and one log line.
- Sales and purchases are never mixed: a question with sales words only selects no purchases scenario.
- The same question gives the same result every time (no randomness, no network).
- `match` makes no outside calls; `test_no_outside_calls` lists none.
- `eval` reports the numbers above; the phase records them in `notes.md` with their limits, and the result is compared with the Laya test (3 and 6 exactly right of 34) before the phase closes.

## Out of scope
Slots (periods, numbers, names), fetching data, answers, any model (Laya, Ollama), the web app, retiring sami-agents, saving answers.

## Depends on
Nothing new (merged `token-verification`, `structured-logging`). The owner supplies about 50 real manager questions; they are added to the evaluation as soon as they arrive and decide which scenarios are written first.

## Open items for the owner
1. The first scenarios to write beyond the 16 in `reference/scenarios.json` (needs the real questions).
2. Port 8006 and the name `intent-api` are assumed.
3. Is it acceptable that `unanswered.jsonl` keeps manager questions on the server's disk?
