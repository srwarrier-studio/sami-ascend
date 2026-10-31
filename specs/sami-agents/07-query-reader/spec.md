# sami-agents/07 query-reader

## Goal
A manager can ask any question in their own words. A local model turns it into a small structured query over what the data can do, code checks the query and fetches the data, and templated sentences built from that data answer it. What the system cannot yet do is said exactly, and logged.

## Why
Phase 06 reads three things (intent, metric, direction) and refuses scope, other periods and anything else. A case tree (the first draft of this spec) would need the owner to add a branch for every new kind of question, which is a menu and not AI Mode. Forum reports of small models doing this rely on: a JSON schema with constrained decoding, the vocabulary in the prompt, a semantic layer in code, and validate-and-retry. We have measured only small models so far: `qwen2.5:1.5b` with a schema got all four slots right on 67 of 89 questions (3.2 s each); `gemma3:270m` to `granite3.1-moe:3b` were not good enough for rewriting text.

## Behavior
### The plan and the query
A question becomes a **plan**: a list of at most 4 queries (`MAX_STEPS`), run in order. "Sales of August compared with the last three months and the largest customer in the period" is two queries: sales for August compared with the previous three months, and customers ranked by sales over the period, top 1. A named period is written once and later steps refer to it; code turns it into dates. When "the period" could mean more than one thing the answer says which it used ("largest customer in August"), and the model's doubt becomes a clarifying question. A question needing more than 4 steps gets the first 4 answered and says the rest must be asked separately.

Each `Query` holds: `metric`, `operation` (`value`, `compare`, `trend`, `rank`, `explain`, `list`), `split_by` (a registry dimension or none), `filters` (dimension to linked entity), `period` (a month or a date range), `compare_with` (previous period, same period last year, a range such as the previous 3 months with `total` or `average`, or none), `top` (a number). It is validated against the registry: unknown metric, dimension or entity, or a period in the future, is rejected before any data is fetched.

### Reading (model fills, code checks)
1. **Capabilities in the prompt.** The prompt lists the registry's metrics, their words from `understanding.json`, their dimensions, the operations and today's date. A new metric or dimension in the registry changes what can be asked with no code change.
2. **Model.** A local model (Ollama, chosen by measurement below) answers with Ollama's own JSON schema `format` (enums for operation, metric, dimension and comparison; no new library: Outlines was considered and not needed, it would bring torch into the workspace for what Ollama already does) and returns entity mentions as free text such as "acme"; Laya may still decide the coarse intent first (other, widgets, business question). Off or down: the phase 06 reader runs unchanged.
3. **Entities.** Customer, supplier and material names are found by code against the real names (synapse-api, cached, `difflib` for typos, whole words, longest wins) and put into `filters`; the model never invents a name. Two equal matches ask which one.
4. **Periods.** Rules read months and common phrases with fuzzy matching; the model fills the rest. Anything it returns must be a real past period.
5. **Validate, retry once.** An invalid query is sent back to the model once with the error; still invalid: ask the manager a clarifying question (`problem: "clarify"` with a short question), never guess.

### Answering (code, from data)
- A plan answers step by step under one answer, blocks in order. A step the data cannot do is reported on its own and the other steps are still answered.
- One `QueryExecutor` runs any valid query through synapse-api (`compare`, `month`, `trend`, `records`) and builds blocks (`text`, `trend`, `table`, `evidence`) with templated sentences. Every number and name comes from the data.
- `explain` uses the existing analyst and graph walk. `value` uses the phase 03 figure. New: filters, `split_by`, `rank`, other periods, and `compare_with`.
- A valid query the data cannot answer (for example no budget metric) answers exactly which part is missing and is appended to a local `unanswered.jsonl` with the query, so the owner sees what to register or build next. `sami-agents unanswered` lists them grouped.
- The answer shows how the question was read (the query in plain words) so a misreading is visible.

### Model choice and evaluation
- First task: measure candidates (`qwen2.5:1.5b`, `gemma3` 4B and 12B if they fit, others the owner names) on the schema task: accuracy per slot and fully right (single and multi-part questions), seconds per question, memory.
- `case-eval` becomes `query-eval`: the 69 existing questions, a set of multi-part questions and the owner's real questions, expected queries written before tuning, a held-out part not looked at until the end, wrong answers counted separately from clarifications. Results go into `notes.md` with their limits.

## Acceptance cases
- Every phase 06 acceptance question still answers the same.
- "I need sales of August compared to the last three months and the largest customer in the period" returns two answered steps, with the period used stated; a fifth part is reported as not answered.
- "sales to Acme in August" returns the filtered figure; "top 5 suppliers by spend last quarter" returns a ranked table for the quarter; "compare purchases with last year" compares with the same period last year.
- A typo in a name links the right entity; an unknown name is not linked and is asked about.
- An invalid query is retried once, then a clarifying question is returned, never a guess.
- A valid query with no data support answers what is missing and is logged once.
- A new metric in the registry is askable with no code change.
- Model off or down: phase 06 behavior.
- No outside calls; the hosts are Laya and Ollama from settings; `test_no_outside_calls` lists them.

## Open items for the owner
1. About 50 real manager questions, any wording: they become the evaluation set.
2. Is it acceptable that sami-agents reads customer, supplier and material names through synapse-api with the user's token?
3. Is it acceptable that `unanswered.jsonl` keeps manager questions on the server's disk?
4. Which models are allowed on the server, and is a GPU available there? CPU only limits us to small models.

## Small change in synapse-web
Show the clarifying question with the choices as buttons, the "how I read it" line and the missing-part text. Separate phase if it grows past one task group.

## Out of scope
A model writing figures, causes or sentences; several metrics in one question; saving an answer to a board; streaming; tone rephrase.

## Depends on
sami-agents 06, 05 and 04 (merged), synapse-api 09, synapse-web 12.
