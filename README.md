# sami-ascend

Every service runs from the root `compose.yaml`.

| Service | Port | What it is |
|---|---|---|
| `auth-api` | 8001 | sign-in, users, roles |
| `workspace-api` | 8002 | workspace forms and requests |
| `mock-sap` | 8003 | the mock SAP (butterfly) |
| `synapse-api` | 8004 | Synapse data and boards |
| `intent-api` | 8006 | reads management questions |
| `intent-classifier` | 8011 | Laya, the domain classifier (`Training/sap-intent-v2`) |
| `workspace-web` | 5173 | workspace app |
| `synapse-web` | 5174 | Synapse app |
| `admin-web` | 5176 | admin app |

Secrets come from the repo `.env`; `auth.db` at the repo root is the users database.

```
docker compose up -d --wait              # start everything, in order, until healthy
docker compose up -d --wait intent-api   # one service and what it needs
docker compose ps                        # status
docker compose logs -f synapse-api       # follow a service
docker compose watch                     # developer mode: file changes go into the running containers
docker compose down                      # stop (data is kept; `down -v` deletes the volumes)
```

`watch`: Vite apps hot-reload; a Python change syncs and restarts only that service; a lockfile or `pyproject.toml`/`package.json` change rebuilds it.

Tests run on the host: `uv run --package <app> --with pytest python -m pytest apps/<app>` and `pnpm --filter <app> test`.
