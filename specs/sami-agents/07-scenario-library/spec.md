# sami-agents/07 scenario-library

## Goal
AI Mode answers only from a library of scenarios that the owner maintains. Laya tests the manager's question against the scenarios, every scenario at or above the confidence threshold (default 70%) is run, and their answers are joined. If none passes, AI Mode says it cannot answer, shows the nearest scenarios and logs the question. Every answer therefore comes from a path a person approved.

## Why
The phase 06 reader handles one metric, one month and a "why" or a figure, and refuses the rest. A tree of cases and a free-form planner were both considered: the tree is a menu, and the planner lets a small model decide what to fetch, which is the least reliable part. The owner chose a library with a confidence gate: a wrong answer is worse than "I cannot answer that yet", and the library grows from the logged refusals.

## Behavior
### The library (`apps/sami-agents/scenarios.toml`, owner maintained)
A scenario has an `id`, a `category` (sales, purchases, ...), a `description` for Laya, `examples` (sample prompts), `slots` (what it needs: `period`, `entity` of a type, `top`, `compare`), the `data` it fetches (a synapse-api call: compare, month, trend or records, with parameters from the slots), the `blocks` it draws (text, trend, table, evidence) and its sentence `template`. Today's figure and why answers are the first two scenarios. A new metric or dimension in the registry plus a scenario entry is all a new question type needs; the code knows no flow.

### Matching (Laya, with a gate)
1. **Category** first: Laya chooses the categories the question touches (one or more, plus `none`). This keeps each following test small.
2. **Scenario** within each chosen category: Laya gives a relevance confidence for each scenario of that category against the whole question (the same check as the widget relevance, per scenario).
3. **Gate.** Scenarios at or above `SCENARIO_MIN_CONFIDENCE` (0.7) are selected. A scenario that declares it `covers` another (for example "compare with previous months" covers "value") suppresses the covered one when both pass, so the manager does not get the same figure twice. At most 4 scenarios run (`MAX_SCENARIOS`); more get the highest four and a note.
4. **None passes:** `problem: "cannot_answer"` with the text "I cannot answer that yet", the two nearest scenarios as "did you mean" choices, and the question appended to a local `unanswered.jsonl`. Laya down or off: the phase 06 reader runs as it does now.

### Slots (code first, model only as a checked backup)
- Months and periods by rules with fuzzy matching; customer, supplier and material names by an `EntityLinker` against the real names from synapse-api (cached, `difflib` for typos, whole words, longest wins); numbers like "top 5" by rules.
- Several selected scenarios share the same slots from the same text ("the period" is one value). If a needed slot is missing or ambiguous, the answer asks for it (`problem: "clarify"`, with choices when known), never guesses.
- Optional fallback for loose period phrasing: `OLLAMA_MODEL` with a JSON schema (Ollama's `format`, no new library; Outlines considered and not needed). Its result is accepted only if it is a real past period. Off when blank.

### Answer
Blocks of each selected scenario in the order their key words appear in the question (ties: library order), under one answer. The answer says how the question was read: the scenarios used, the slot values, and, if a scenario was dropped, why. All numbers and names come from the data; the model writes none.

### Maintenance and evaluation
- `sami-agents scenarios check` (every `data` call exists in the registry, slots are known, examples present, sibling descriptions that overlap, `covers` has no loop) and `scenarios show` (the library as a table), and `sami-agents unanswered` (grouped refusals). The how-to goes in `docs/scenarios-maintenance.md`.
- `scenario-eval`: the 69 existing questions, a set of multi-part questions and the owner's real questions, expected scenarios written before tuning, a held-out part not looked at until the end. It reports, at the gate, how many questions got exactly the right scenarios, how many got a wrong or extra one, how many were refused, and the same for several thresholds so 70% is chosen with numbers, not assumed.

## Acceptance cases
- Every phase 06 acceptance question still answers the same.
- "I need sales of August compared to the last three months and the largest customer in the period" selects the comparison scenario and the top customer scenario, fills August and the shared period, and returns both answers; the plain "sales" scenario is suppressed by `covers`.
- A question matching nothing returns `cannot_answer` with the nearest scenarios and one log line; a question below the threshold is never answered.
- A name with a typo links the right entity; an unknown name is not linked and is asked about.
- A new scenario added to `scenarios.toml` answers its examples with no code change; `scenarios check` rejects an unknown data call or a `covers` loop.
- Laya off or down: phase 06 behavior.
- No outside calls; Laya and Ollama are the only added hosts, both from settings; `test_no_outside_calls` lists them.

## Open items for the owner
1. About 50 real manager questions: they decide the first scenarios and the evaluation set.
2. Is it acceptable that sami-agents reads customer, supplier and material names through synapse-api with the user's token?
3. Is it acceptable that `unanswered.jsonl` keeps manager questions on the server's disk?
4. Laya must run where the service runs; is the server allowed to run it (Python 3.13, CPU torch)?

## Small change in synapse-web
Show `cannot_answer` with the nearest scenarios, the clarifying choices and the "how I read it" line. Separate phase if it grows past one task group.

## Out of scope
A model writing figures, causes or sentences; a free-form planner (a later best-effort tier if management wants wider coverage); saving an answer to a board; streaming; tone rephrase.

## Depends on
sami-agents 06, 05 and 04 (merged), synapse-api 09, synapse-web 12.
