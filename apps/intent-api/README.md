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

Settings: `DOMAIN_MIN_PROBABILITY` (0) and `SCENARIO_MIN_PROBABILITY` (0.3), both chosen with the evaluation, and `MAX_SCENARIOS` (4).

## Evaluation
`evals/questions.json` holds the questions (`id`, `question`, `part` single, multi or refuse, expected `domain`, expected `scenarios`, `heldout`). Questions with no scenarios must be refused: other domains that have no scenarios yet, forecasts, and anything not about the business. About a third are held out. With Laya running:

```
LAYA_URL=http://localhost:8011 uv run --package intent-api intent-api eval [--show] [--domain-min 0.4 --scenario-min 0.3]
```
It prints, for the chosen floors and for a grid of others, how many answerable questions were exactly right, had a wrong or extra scenario, or were missing one or wrongly refused, and how many must-refuse questions were refused or wrongly answered. It uses the tuning questions only; `--final` also runs the held-out ones once, with the chosen floors. Keep real manager questions out of this file unless the owner adds them on their own machine.
