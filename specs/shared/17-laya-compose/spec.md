# shared/17 laya-compose

## Goal
Laya, the domain classifier intent-api depends on, starts with the rest of the dev services from one command and keeps its model files in persistent storage, so it is never the missing part again.

## Why
intent-api answers `503 cannot_classify_now` when Laya is down, and synapse-web then falls back to a keyword match on widget titles, which shows unrelated widgets (2026-11-06). `scripts/dev.sh` only started Laya when `~/laya-env/bin/laya-serve` existed, and it did not on this machine. Laya is not part of the repo, so every new machine or clean checkout loses it.

## Behavior
- **`compose.yaml` at the repo root** with one service, `laya`:
  - Image built from `infra/laya/Dockerfile`: Python 3.14, torch from the CPU index (no CUDA libraries), `laya[serve]`, running `laya-serve` on `0.0.0.0:8011` inside the container.
  - Published as `127.0.0.1:8011:8011`, so intent-api on the host reaches it at `http://localhost:8011` unchanged and nothing outside the machine can.
  - The fine-tuned checkpoint `Training/sap-intent-v2` is mounted read-only; a new checkpoint from Colab is copied there and the service restarted, with no rebuild. The model name, default model and extra-model settings are the same as `scripts/dev.sh` used (`sap-intent-v2`).
  - A named volume holds Laya's cache (downloads), so a rebuilt or recreated container does not download again.
  - `restart: unless-stopped` and a health check on the port, so `docker compose up -d --wait laya` returns when Laya is ready.
- **`scripts/dev.sh`:** `start` runs `docker compose up -d --wait laya` first and no longer looks for `laya-env`; if Docker is missing or the checkpoint folder is missing it says so in one clear line and carries on (intent-api then answers `cannot_classify_now`). `stop` stops the container; `status` still reports port 8011.
- **Docs:** the Laya section of `apps/intent-api/README.md` replaces the host `laya-env` steps with the compose steps (the host steps stay as a short fallback); the root README or notes get the one command.
- **No secrets:** `LAYA_API_KEY`, if used, comes from the repo `.env`, never from the image or compose file.
- **Not built:** the other services in compose, training in a container (training stays on Colab), GPU support, any change to intent-api, synapse-web or Laya itself.

## Acceptance cases
- From a clean state, `docker compose up -d --wait laya` ends with the container healthy and `GET http://localhost:8011/` answering.
- `intent-api` `domain "What were sales for August?"` prints Sales with a probability, with no change to its settings.
- After `docker compose down` and `up`, Laya is ready again without downloading anything.
- Replacing the files in `Training/sap-intent-v2` and restarting the service serves the new model, without rebuilding the image.
- `scripts/dev.sh start` brings Laya up, and `status` shows `up laya (8011)`; with Docker stopped it prints the one-line reason and the other services still start.

## Out of scope
The rest of the stack in compose (a later phase), the synapse-web message when intent-api is down (a small synapse-web phase), changes to the Laya package or its model.

## Depends on
The `Training/sap-intent-v2` checkpoint (ignored by git, kept on the owner's machine).
