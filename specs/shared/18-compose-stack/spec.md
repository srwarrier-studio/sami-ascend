# shared 18 compose-stack

## Goal
Every service of the app runs from the root `compose.yaml`: one command starts or stops the whole stack, in the right order, and a developer watch mode puts source changes into the running containers without rebuilding or recreating them. `scripts/dev.sh` goes away.

## Why
Services were started by a shell script and a hand-installed Laya; missing parts (Laya not installed) gave silent wrong behavior. shared 17 moved Laya into compose; the owner wants to start and stop everything with Docker from now on.

## Behavior
- **Names say the purpose, never the technology**, so a part can be swapped without renaming: the mock SAP (butterfly) is `mock-sap`, Laya is `intent-classifier`; images, volumes and `infra/` folders follow (`infra/classifier`, `infra/api`, `mock-sap-data`, `classifier-cache`). Application settings keep their own names (`LAYA_URL`).
- **Services in `compose.yaml`**, each with its own image and the ports it has today, bound to `127.0.0.1`: `auth-api` 8001, `workspace-api` 8002, `mock-sap` 8003, `synapse-api` 8004, `intent-api` 8006, `intent-classifier` 8011, `workspace-web` 5173, `synapse-web` 5174, `admin-web` 5176. Browser URLs and the `VITE_*` defaults do not change.
- **Images.** The five Python APIs share one build of the uv workspace (Python 3.14, `uv sync` from `uv.lock`, no dev tools in the runtime layer) with a different command per service; the three web apps share one Node image with the pnpm workspace installed from `pnpm-lock.yaml` and run `vite --host 0.0.0.0`.
- **Wiring by name.** Calls between services use compose names through their existing settings: `intent-api` to `LAYA_URL=http://intent-classifier:8011` and `SYNAPSE_URL=http://synapse-api:8004`; `synapse-api` and `workspace-api` to `http://mock-sap:8003/...` for every SAP base URL. Each API's `FRONTEND_URL` is its web app's origin (as `dev.sh` set it).
- **Secrets and config** come from the repo `.env` through `env_file`; nothing secret is in an image or in the compose file. `JWT_SECRET` stays the shared token secret.
- **Order and health.** Each service has a health check; `depends_on` with `condition: service_healthy` starts mock-sap and intent-classifier before the services that call them, and the web apps last. `docker compose up -d --wait` returns when all are healthy.
- **Data.** `auth.db` stays the owner's real file at the repo root, bind-mounted; mock-sap's and workspace-api's SQLite files and `unanswered.jsonl` live in named volumes or bind mounts the spec for each service states; `docker compose down` keeps all data, only `down -v` removes named volumes.
- **Watch mode.** `docker compose watch` (or `up --watch`): web sources are synced and Vite hot-reloads; Python sources are synced and the service process restarts inside the same container (`sync+restart`); a change to `pyproject.toml`, `uv.lock`, `package.json` or `pnpm-lock.yaml` rebuilds that service. No change needs `down` or `up`.
- **Profiles.** `ai` (intent-classifier, intent-api) and `web` (the three web apps) can be left out, e.g. `docker compose up -d --wait --profile core`; plain `up` starts everything.
- **`scripts/dev.sh` is removed**; the README and the intent-api README say `docker compose up -d --wait` (start), `docker compose ps` (status), `docker compose down` (stop), `docker compose logs -f <service>`. Host-run `uv run ...` and `pnpm ...` keep working for tests and one-off use.
- **Not built:** production images, TLS, a reverse proxy, running the test suites in containers, Colab training, GPU.

## Acceptance cases
- From stopped, `docker compose up -d --wait` ends with every service healthy and the owner can sign in on 5173, 5174 and 5176 as before.
- A question in synapse-web AI Mode reaches intent-api, Laya and synapse-api and is answered; a workspace sales order and a customer create go through workspace-api to butterfly.
- `docker compose down` then `up` keeps `auth.db` users and the butterfly and workspace data.
- With `docker compose watch` running, editing a Python file restarts only that process within seconds and the container id does not change; editing a React file hot-reloads the page; editing `uv.lock` rebuilds that service.
- Stopping `intent-classifier` makes `intent-api` answer `cannot_classify_now` and AI Mode shows the unavailable message with Try again; starting it again recovers without restarting the others.
- The host test suites still run as before.

## Out of scope
Production deployment, CI images, replacing SQLite, moving SAP URLs for the real SAP (settings keep their env names).

## Depends on
shared 17 (Laya service, compose file).
