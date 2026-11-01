# intent-api

Reads a manager's question and decides which approved scenarios it asks for, using fixed rules only. No model is called. Nothing is answered yet (see `specs/intent-api/`).

## Run
`uv run --package intent-api intent-api` (port 8006). Needs `JWT_SECRET` in the repo-root `.env`. `GET /v1/intent/health` answers without a login.

## Test
`uv run --package intent-api --with pytest python -m pytest apps/intent-api`
