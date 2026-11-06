# Tasks

- [ ] 1. Image and compose: `infra/laya/Dockerfile` (CPU torch, `laya[serve]`) and `docker-compose.yml` with the checkpoint mount, cache volume, port, restart and health check. Done when `docker compose up -d --wait laya` is healthy and `intent-api domain` classifies a question.
- [ ] 2. `scripts/dev.sh` and docs: start, stop and status use compose, clear message without Docker or checkpoint, intent-api README and notes updated. Done when `dev.sh start` brings Laya up and a down/up cycle needs no download.
