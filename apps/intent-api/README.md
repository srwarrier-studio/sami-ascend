# intent-api

Reads a manager's question and decides which approved scenarios it asks for, using fixed rules only. No model is called. Nothing is answered yet (see `specs/intent-api/`).

## Run
`uv run --package intent-api intent-api` (port 8006). Needs `JWT_SECRET` in the repo-root `.env`. `GET /v1/intent/health` answers without a login.

## Test
`uv run --package intent-api --with pytest python -m pytest apps/intent-api`

## Laya (the domain classifier)
intent-api asks Laya which domain a question belongs to (`scenarios.toml` lists the domains). Laya runs as its own process; it is not a dependency of this app. On the host:

```
uv venv --python 3.14 laya-env
uv pip install --python laya-env/bin/python torch --index-url https://download.pytorch.org/whl/cpu
uv pip install --python laya-env/bin/python "laya[serve]"
LAYA_HOST=127.0.0.1 LAYA_PORT=8011 LAYA_MODELS=typed-decisions laya-env/bin/laya-serve
```
Install torch from the CPU index first so the CUDA libraries are not pulled in. The first start downloads the checkpoint. Then set `LAYA_URL=http://localhost:8011` (and `LAYA_API_KEY` if the server has one; `LAYA_MODEL` defaults to `typed-decisions`) and try:

```
uv run --package intent-api intent-api domain "What were sales for August?"
```
It prints the domain and its probability, `refused (Other)` when Laya says the question is not about the business, or `cannot_classify_now` when Laya cannot be reached. Notes on Laya are in `docs/laya/`.

## Scenario library
`scenarios.toml` lists the domains (`[domain.<Name>]` with a short description) and the approved scenarios (`[[scenario]]` with `id`, `domain`, `description`, `examples`, `needs`, `covers`). `uv run --package intent-api intent-api scenarios check` validates it and `scenarios show` prints it by domain. A new kind of question is a new `[[scenario]]` entry; the code knows no flow.

## Match
`POST /v1/intent/match` with `{"question": "..."}` (management or admin cookie). It asks Laya for the domain, then for the scenarios of that domain, and returns the domain with its probability and every domain's score, the scenarios offered, and the selected scenarios with their probabilities. A refusal is `200` with `problem: "cannot_answer"`, a `reason` (`not_about_business`, `not_sure`, `no_scenarios`, `nothing_matched`) and `did_you_mean` (the two nearest domains); it is also appended to `unanswered.jsonl` (setting `UNANSWERED_LOG`, ignored by git). When Laya cannot be reached the answer is `503` with `problem: "cannot_classify_now"`. `uv run --package intent-api intent-api unanswered` lists the refused questions by nearest domain.

Settings: `DOMAIN_MIN_PROBABILITY` (0.4) and `SCENARIO_MIN_PROBABILITY` (0.3), both chosen with the evaluation, and `MAX_SCENARIOS` (4).

## Evaluation
`evals/questions.json` holds the questions (`id`, `question`, `part` single, multi or refuse, expected `domain`, expected `scenarios`, `heldout`). Questions with no scenarios must be refused: other domains that have no scenarios yet, forecasts, and anything not about the business. About a third are held out. With Laya running:

```
LAYA_URL=http://localhost:8011 uv run --package intent-api intent-api eval [--show] [--domain-min 0.4 --scenario-min 0.3]
```
It prints, for the chosen floors and for a grid of others, how many answerable questions were exactly right, had a wrong or extra scenario, or were missing one or wrongly refused, and how many must-refuse questions were refused or wrongly answered. It uses the tuning questions only; `--final` also runs the held-out ones once, with the chosen floors. Keep real manager questions out of this file unless the owner adds them on their own machine.

## Answers
`POST /v1/intent/answer` with `{"question": "..."}` (management or admin cookie) reads the question as `/match` does, then builds one answer per selected scenario from `answers.toml` (scenario key, `response` of `value`, `compare`, `trend` or `ranking`, the `metric`, `against` for a compare and `by` for a ranking; `uv run --package intent-api intent-api answers check` validates it). The response has `reading` (the `/match` body), `answers` (`scenario` and `blocks`: `text` lines, `trend` points, `table` rows, the same shapes sami-agents returns) and, for a refusal, `problem: "cannot_answer"`, a `reason` and `periods`. New reasons: `not_answerable_yet` (no entry in `answers.toml`, for example every `why`) and `period_not_supported` (more than one period, or one that has not started). The period is read by rules from the whole question: a month, `last month`, `this month`, `last year`, `this year`, a year, none meaning the last finished month. Figures come from synapse-api (`SYNAPSE_URL`, default `http://localhost:8004`) with the caller's cookie; when it cannot be reached the answer is `503` with `problem: "cannot_fetch_now"`. A ranking reads the 50 members whose figure changed most and shows the top 5 by value (`TOP_RANKED`).

## Training data (for fine-tuning Laya on Google Colab)
`Training/families.toml` holds invented slot values and question families (one meaning said in different ways); nothing in it is a real name or figure. `uv run --package intent-api intent-api training build [--fraction 0.5] [--seed N]` expands it, with a fixed seed, into `Training/out/train.jsonl` and `Training/out/heldout.jsonl` (ignored by git): one row per item in the same form the app sends to Laya (the question as `{"question": text}`, the same instructions and short option descriptions), domain items and scenario items, spelling mistakes added, two-clause questions, and some scenario items that offer only some of the scenarios. Every fourth family of a group is held out, no question from `evals/questions.json` is used, and the files pass Laya's own `dry_run`.

`intent-api training check` runs the checks (no overlap between training and held-out families or with the evaluation questions, every domain and scenario taught and tested, balance, refusals at least a fifth, no duplicates or conflicting answers). `Training/intent-training.ipynb` is the notebook for a remote GPU (it stops if there is none): run `training build`, put `Training/out/train.jsonl` and `heldout.jsonl` (invented questions only) next to it, run the cells, and download the zipped checkpoint. Never run it on a laptop. To use the tuned checkpoint, unzip it and start `laya-serve` with `LAYA_EXTRA_MODELS={"intent-tuned-2": "<folder>"}`, then set `LAYA_MODEL=intent-tuned-2` for intent-api.
