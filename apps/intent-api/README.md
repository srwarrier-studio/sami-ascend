# intent-api

Reads a manager's question and decides which approved scenarios it asks for, using fixed rules only. No model is called. Nothing is answered yet (see `specs/intent-api/`).

## Run
`uv run --package intent-api intent-api` (port 8006). Needs `JWT_SECRET` in the repo-root `.env`. `GET /v1/intent/health` answers without a login.

## Test
`uv run --package intent-api --with pytest python -m pytest apps/intent-api`

## The classifier
intent-api asks a classifier which domain and scenario a question belongs to. By default that is `onnx-classifier` (`apps/onnx-classifier`, DeBERTa-v3-small on ONNX Runtime, about 290 MB of memory, port 8012). The address is `LAYA_URL` (default `http://onnx-classifier:8012` in compose):

```
docker compose up -d --wait intent-api
```
The request and response format is Laya's `POST /v1/systemone` (the earlier classifier, removed on 2026-11-07, its checkpoint is on Hugging Face), so the client in `infrastructure/laya_choice_classifier.py` and the `LAYA_*` settings keep that name. If the classifier is down, intent-api answers `cannot_classify_now`.

## Scenario library
`scenarios.toml` lists the domains (`[domain.<Name>]` with a short description) and the approved scenarios (`[[scenario]]` with `id`, `domain`, `description`, `examples`, `needs`, `covers`). `uv run --package intent-api intent-api scenarios check` validates it and `scenarios show` prints it by domain. A new kind of question is a new `[[scenario]]` entry; the code knows no flow.

## Match
`POST /v1/intent/match` with `{"question": "..."}` (management or admin cookie). It asks the classifier for the domain, then for the scenarios of that domain, and returns the domain with its probability and every domain's score, the scenarios offered, and the selected scenarios with their probabilities. A refusal is `200` with `problem: "cannot_answer"`, a `reason` (`not_about_business`, `not_sure`, `no_scenarios`, `nothing_matched`) and `did_you_mean` (the two nearest domains); it is also appended to `unanswered.jsonl` (setting `UNANSWERED_LOG`, ignored by git). When Laya cannot be reached the answer is `503` with `problem: "cannot_classify_now"`. `uv run --package intent-api intent-api unanswered` lists the refused questions by nearest domain.

Settings: `DOMAIN_MIN_PROBABILITY` (0.4) and `SCENARIO_MIN_PROBABILITY` (0.3), both chosen with the evaluation, and `MAX_SCENARIOS` (4).

## Evaluation
`evals/questions.json` holds the questions (`id`, `question`, `part` single, multi or refuse, expected `domain`, expected `scenarios`, `heldout`). Questions with no scenarios must be refused: other domains that have no scenarios yet, forecasts, and anything not about the business. About 60% are held out (the 105 questions seeded from the owner's, source `seeded`, are all held out); 87 are for tuning thresholds. With the classifier running:

```
LAYA_URL=http://localhost:8011 uv run --package intent-api intent-api eval [--show] [--domain-min 0.4 --scenario-min 0.3]
```
It prints, for the chosen floors and for a grid of others, how many answerable questions were exactly right, had a wrong or extra scenario, or were missing one or wrongly refused, and how many must-refuse questions were refused or wrongly answered. It uses the tuning questions only; `--final` also runs the held-out ones once, with the chosen floors. Keep real manager questions out of this file unless the owner adds them on their own machine.

## Answers
`POST /v1/intent/answer` with `{"question": "..."}` (management or admin cookie) reads the question as `/match` does, then builds one answer per selected scenario from `answers.toml` (scenario key, `response` of `value`, `compare`, `trend` or `ranking`, the `metric`, `against` for a compare and `by` for a ranking; `uv run --package intent-api intent-api answers check` validates it). The response has `reading` (the `/match` body), `answers` (`scenario` and `blocks`: `text` lines, `trend` points, `table` rows) and, for a refusal, `problem: "cannot_answer"`, a `reason` and `periods`. New reasons: `not_answerable_yet` (no entry in `answers.toml`, for example every `why`, or a qualifier that cannot be applied, see below) and `period_not_supported` (time words it cannot read, a period that has not started, or more than 6 periods). A refusal carries `message`, a plain sentence naming what was not read and what can be; every answer carries `period_read` (label, start, end, whether the period is complete and a `note`).

### How the period is read
`ReadPeriod` reads it from the whole question, in this order: our own rules (`period_words.toml` holds the words: last, this, to, between and btw, and, year to date, month to date, financial year and the unreadable ones), then dateparser for what is left. Read by the rules: current, present and previous month, MTD, YTD and so far, this and last quarter, Q1 to Q4 and the spelled-out quarters, H1 and H2, `FY 2025-26`, `FY26`, `2025-26`, `this financial year` and `FY Q3` (the financial year runs April to March; a bare `Q3` is the calendar quarter), `since april`, `last 30 days` or `last six months`, ranges (`from april to june`, `between july and september`, `jun, jul and aug`) and a month or a year. Words of five letters or more are corrected when close to a known word (`betwen`, `febuary`). dateparser (a fallback, `DateparserPeriods`) only sees the words the rules did not read; it can give a month or a year, which the reply notes ("I read “a quarter back” as August 2026"); a day or a week is refused by name, because the data is monthly. A question with no period is answered for the last finished month and says so in a first line ("No period was named, so this is October 2026."). Several periods are answered one after the other (up to 6); two periods on a compare question are compared (`september against august`, `Q2 vs Q1`).

### Qualifiers that are not applied
`ReadQualifiers` (words in `qualifier_words.toml`) refuses, with a sentence and `reason: "not_answerable_yet"`, a named customer, supplier, material or country (a capitalised name in the middle of the question, a company marker such as `Ltd` or `m/s`, or a country in the table; a name typed in lowercase is not caught), a quantity or count (`kg`, `orders`, `how many`) and a currency other than rupees and dollars. `top 3` or `top three` shows that many (at most 10); a larger number shows 10 and says so.

Figures come from synapse-api (`SYNAPSE_URL`, default `http://localhost:8004`) with the caller's cookie; when it cannot be reached the answer is `503` with `problem: "cannot_fetch_now"`. A ranking reads the 50 members whose figure changed most and shows the top 5 by value (`TOP_RANKED`).

## Why-questions (company scope and currency)
`sales_why` and `purchases_why` have `response = "why"` in `answers.toml`: "why did sales fall in August" is answered by the analysis (graph, movers, causes, offset) built from synapse-api reads, with no model in the answer. It needs one finished month. The request takes `company` (`all` by default, `sabinsa`, `neutraceuticals` or `organica`), sent to every synapse-api read (a company the user does not have is `403 {"problem": "company_not_allowed"}`); the currency is read from the question (`USD`, `INR`, dollars, rupees, `$`, `₹`) or is the one with the biggest change, and the first sentence names the company and the currency. The graph is `graph.toml` (how-to in `docs/graph-maintenance.md`): `uv run --package intent-api intent-api graph check` validates it against `apps/synapse-api/registry.toml` and the contracts, `graph show [--mermaid]` prints it. `uv run --package intent-api --with-editable apps/butterfly --with-editable apps/synapse-api intent-api why-eval [--final]` asks one question per butterfly scenario in process for `sabinsa` (sales in `USD`, purchases in `INR`) and scores the causes against `apps/butterfly/scenarios/*.json`: all 10 development scenarios pass, and with `--final` 11 of 14 pass (the held-back `two-causes`, `cancellations` and `supplier-switch` are known unsolved). Settings: `SIGNIFICANT_PERCENT`, `MOVER_MIN_PERCENT`, `MOVER_MIN_SHARE`, `PRICE_MAJORITY_PERCENT`.

## Training data (for fine-tuning the classifier on Google Colab)
`Training/families.toml` holds invented slot values and question families (one meaning said in different ways); nothing in it is a real name or figure. `uv run --package intent-api intent-api training build [--fraction 0.5] [--seed N]` expands it, with a fixed seed, into `Training/out/train.jsonl` and `Training/out/heldout.jsonl` (ignored by git): one row per item in the same form the app sends to Laya (the question as `{"question": text}`, the same instructions and short option descriptions), domain items and scenario items, spelling mistakes added, two-clause questions, and some scenario items that offer only some of the scenarios. Every fourth family of a group is held out, no question from `evals/questions.json` is used, and the files pass Laya's own `dry_run`.

`intent-api training check` runs the checks (no overlap between training and held-out families or with the evaluation questions, every domain and scenario taught and tested, balance, refusals at least a fifth, no duplicates or conflicting answers). `apps/onnx-classifier/tools/cross-encoder.ipynb` is the notebook for a remote GPU (Colab); see `apps/onnx-classifier/README.md` for the steps from the Colab export to `Training/classifier-model/`.
