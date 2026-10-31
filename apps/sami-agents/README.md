# sami-agents

AI service for Sami apps. It answers Synapse AI Mode messages with the widgets that fit, as an OpenUI Lang program.

## Run
`uv run --package sami-agents sami-agents` (port 8005). Needs `JWT_SECRET` in the repo-root `.env`, and synapse-api running on `SYNAPSE_URL` (default `http://localhost:8004`) for the widget catalog.

## How it picks widgets
1. The keyword search proposes widgets, using word stems and `aliases.json` (extra words for each widget; edit it when users ask for something and get no answer).
2. Optionally, Laya checks each proposal (see below). Without Laya every proposal is accepted, up to 4 widgets for a question and 15 for `@builder`.
3. A sentence and the widgets are returned as OpenUI Lang.

## Evaluate
`uv run --package sami-agents sami-agents eval [--parallel 4] [--no-check] [--aliases none] [--prompts apps/sami-agents/evals/heldout.json]` runs the prompts in `evals/` and prints how many the keyword search alone and the whole pipeline get right. Add real questions that failed to `evals/prompts.json`.

## Laya (optional, off by default)
Laya is a small classification model (https://huggingface.co/convaiinnovations/laya, Apache 2.0). With the aliases in place it did not beat the keyword search in our tests, so it is off unless `LAYA_URL` is set. To try it, run it outside the workspace (it needs Python 3.13 and torch):

```
uv venv --python 3.13 laya-env
uv pip install --python laya-env/bin/python torch --index-url https://download.pytorch.org/whl/cpu
uv pip install --python laya-env/bin/python "laya[serve]"
LAYA_API_KEY=<secret> LAYA_HOST=127.0.0.1 LAYA_MODELS=typed-decisions laya-serve
```
Install torch from the CPU index first so the CUDA libraries are not pulled in. Then set `LAYA_URL=http://localhost:8000`, `LAYA_API_KEY=<secret>` (and optionally `LAYA_THRESHOLD`, default 0.35) for `sami-agents`. If Laya is unreachable the service answers from the keyword search.

## Settings
`JWT_SECRET`, `FRONTEND_URL`, `SYNAPSE_URL`, `LAYA_URL`, `LAYA_API_KEY`, `LAYA_THRESHOLD`, `LAYA_TIMEOUT_SECONDS`, `OLLAMA_URL`, `OLLAMA_MODEL`, `MODEL_TIMEOUT_SECONDS`.
