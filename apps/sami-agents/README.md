# sami-agents

AI service for Sami apps. It answers Synapse AI Mode messages with the widgets that fit, as an OpenUI Lang program.

## Run
`uv run --package sami-agents sami-agents` (port 8005). Needs `JWT_SECRET` in the repo-root `.env`, and synapse-api running on `SYNAPSE_URL` (default `http://localhost:8004`) for the widget catalog.

## How it picks widgets
1. The keyword search proposes widgets, using word stems and `aliases.json` (extra words for each widget; edit it when users ask for something and get no answer).
2. Optionally, Laya checks each proposal (see below). Without Laya every proposal is accepted, up to 4 widgets for a question and 15 for `@builder`.
3. A sentence and the widgets are returned as OpenUI Lang. The sentence is built from the widget titles (`Here is Top customers and Top materials.`).
4. Optionally a small model can write that sentence instead (see below).

## Evaluate
`uv run --package sami-agents sami-agents eval [--parallel 4] [--no-check] [--aliases none] [--prompts apps/sami-agents/evals/heldout.json]` runs the prompts in `evals/` and prints how many the keyword search alone and the whole pipeline get right. Add real questions that failed to `evals/prompts.json`.

## The graph
`graph.toml` says what relates to what and what counts as unusual (see `docs/graph-maintenance.md`). `uv run --package sami-agents sami-agents graph check` validates it against `apps/synapse-api/registry.toml` and the contracts in `docs/sap/`; `graph show [--mermaid]` prints it. The walk (`WalkGraph`) follows it from a mover to what is unusual behind it (`root_cause`), after it (`impact`), or around it (`dependency`), reading only through synapse-api with the user's own cookie.

## Laya (optional, off by default)
Laya is a small classification model (https://huggingface.co/convaiinnovations/laya, Apache 2.0). With the aliases in place it did not beat the keyword search in our tests, so it is off unless `LAYA_URL` is set. To try it, run it outside the workspace (it needs Python 3.13 and torch):

```
uv venv --python 3.13 laya-env
uv pip install --python laya-env/bin/python torch --index-url https://download.pytorch.org/whl/cpu
uv pip install --python laya-env/bin/python "laya[serve]"
LAYA_API_KEY=<secret> LAYA_HOST=127.0.0.1 LAYA_MODELS=typed-decisions laya-serve
```
Install torch from the CPU index first so the CUDA libraries are not pulled in. Then set `LAYA_URL=http://localhost:8000`, `LAYA_API_KEY=<secret>` (and optionally `LAYA_THRESHOLD`, default 0.35) for `sami-agents`. If Laya is unreachable the service answers from the keyword search.

## Sentence writer (optional, off by default)
Set `OLLAMA_MODEL` (for example `LiquidAI/lfm2.5-1.2b-instruct`) to let a local Ollama model write the sentence. The text is only used if it passes strict checks (one line, under 200 characters, no markup, no digits, names a widget being shown and has at least two other words); otherwise the title-built sentence is used. In our test the model often failed these checks and added about 2 seconds, and larger models invented what widgets show, so it is off by default.

## Settings
`JWT_SECRET`, `FRONTEND_URL`, `SYNAPSE_URL`, `LAYA_URL`, `LAYA_API_KEY`, `LAYA_THRESHOLD`, `LAYA_TIMEOUT_SECONDS`, `OLLAMA_URL`, `OLLAMA_MODEL`, `MODEL_TIMEOUT_SECONDS`.
