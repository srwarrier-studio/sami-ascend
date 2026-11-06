# Tasks

- [x] 1. Image and compose: `infra/laya/Dockerfile` (CPU torch, `laya[serve]`) and `compose.yaml` with the checkpoint mount, cache volume, port, restart and health check. Done when `docker compose up -d --wait laya` is healthy and `intent-api domain` classifies a question.
- [x] 2. `scripts/dev.sh` starts and stops Laya through compose (one-line message without Docker or checkpoint) and the intent-api README gets the compose steps; the rest of `dev.sh` is replaced in shared 18. Done when `dev.sh start` brings Laya up.
