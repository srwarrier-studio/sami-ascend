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
