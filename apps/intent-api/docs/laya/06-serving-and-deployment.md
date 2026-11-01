# Serving and deployment

## HTTP server: `laya-serve`
`pip install "laya[serve]"`, run `laya-serve` (port 8000 by default). Protocol is the TypeSafe Jev `/v1/systemone` wire format.

### Auth
- With `LAYA_API_KEY` set, every route needs `Authorization: Bearer <key>`, and `/docs`, `/redoc`, `/openapi.json` are disabled.
- With no key, the API has no authentication. Our local server on port 8000 may be running either way; check before relying on it.
- `GET /health` is always open; without a valid bearer it returns only `{"status": "ok"}`. It does not run inference, so it proves the process is up, not that a model works.
- The in-process library (`laya.load`) needs no key and no server.

### Endpoints
- `GET /health`: `status`, `loaded`, `revisions`, `device`, `checkpoint_devices`, `cpu_fallbacks` (authenticated callers).
- `POST /v1/route`: which checkpoint would be chosen, no inference. Body: `state`, `questions`, optional `model`, `task`, `lang`, `lang_guess`, `explain`.
- `POST /v1/systemone`: one state, many questions.
- `POST /v1/systemone/batch`: one question set over `states`; splits into several passes when `states x questions x width` exceeds `LAYA_MAX_BATCH_TOKENS`.

`/v1/systemone` request: `state` (required), `questions` (required; each with `type`, `instructions`, `criteria`), optional `model`, `task`, `lang`, `lang_guess`, `max_len`, `head_max_len`, `min_confidence`. Hook arguments are rejected with 422. Our existing client for it is `apps/sami-agents/.../laya_case_model.py` (it sends `{"state": {"request": text}, "questions": {...}, "model": "typed-decisions"}`).

Response: `model`, `answers`, `usage`, `routing`. Per answer: `choice` has `choice`, `probabilities`, `x_jev_confidence`; `score` has `score`, `probabilities` keyed "0".."k-1", `legend`; `noul` has `noul`. All have `type`, `confidence`, `answer_confidence`, `action.act_probability`. With `min_confidence`: `abstention`, `abstention_threshold`, `low_confidence`. Headers: `Server-Timing`, `X-Inference-Time-Ms`.

Errors: 400 bad body; 401 bad bearer; 408 body not delivered in `LAYA_BODY_READ_TIMEOUT`; 413 size limit; 422 invalid question, unsupported control, or unknown model; 500 inference failure; 503 over `LAYA_MAX_CONCURRENT` (retry-after 1).

Limits: body 2 MiB; state 50,000 chars; 64 questions; 64 states per batch; 100 options per choice (255 with tournament); 32 score levels; 512 options per request. Inference runs on a single worker (one forward pass at a time); admission is refused rather than queued.

Strict Jev mode `LAYA_JEV_STRICT=1` strips the response down to the Jev contract and drops `answer_confidence`, which changes calibration metrics (the docs show ECE moving 0.09 to 0.17).

`LAYA_TOURNAMENT_GROUP` (2 to 100) enables elimination for choices larger than the group.

### Environment variables
`LAYA_HOST` (0.0.0.0), `LAYA_PORT` (8000), `LAYA_ROOT_PATH`, `LAYA_DEVICE`, `LAYA_PRELOAD` (1), `LAYA_MODELS`, `LAYA_THREADS`, `LAYA_AUTO_TASK` (0), `LAYA_IDLE_UNLOAD_SECONDS` (0), `LAYA_MAX_LOADED` (2), `LAYA_MAX_TOKEN_BUDGET` (8192), `LAYA_DEFAULT_MODEL` (multilingual), `LAYA_EXTRA_MODELS` (JSON), `LAYA_API_KEY`, `LAYA_LOG_LEVEL`, `LAYA_MAX_CONCURRENT` (16), `LAYA_BODY_READ_TIMEOUT` (10), `LAYA_MAX_BATCH_TOKENS` (131072), `LAYA_JEV_STRICT`, `LAYA_TOURNAMENT_GROUP`.

## CLI
`laya "<text>"` routes only (offline). `--predict` runs a prediction (first run downloads weights). Flags: `--json`, `--model english|multilingual|typed-decisions`, `--lang`, `--lang-guess`, `--task`, `--device`, `--preset email|guard|moderation|router|triage`. No text opens an interactive prompt. Also `laya eval` and `laya train`. Failures exit with code 2.

## MCP (stdio)
`pip install "laya[mcp]"`, run `laya-mcp-server`. Tools: `laya_status`, `laya_route`, `laya_predict`, `laya_shortlist`, `laya_tournament`, `laya_preset`, `laya_predict_batch`, `laya_route_batch`, `laya_decide`, `laya_predict_long`. Set `LAYA_BASE_URL` to share one HTTP model server among clients (shortlist, tournament and long-text tools are then unsupported). Hooks are not installed by the stock launcher.

## Docker
Needs Docker with Compose v2; CPU quickstart needs 8 GB RAM and 10 GB disk. Commands: `docker compose run --build --rm laya` (one-shot), `docker compose -f compose.yaml -f compose.http.yaml up --build laya-serve` (HTTP; add `compose.cuda.yaml` for NVIDIA, `compose.spark.yaml` for DGX Spark). The API publishes on `127.0.0.1` by default; to expose it set `LAYA_API_KEY` first, then `LAYA_BIND_ADDRESS=0.0.0.0`, behind a TLS proxy. Prefer `LAYA_API_KEY_FILE` / `HF_TOKEN_FILE` over raw secrets. The image runs as UID 10001; the model cache volume is `/home/laya/.cache/huggingface`. Custom checkpoint: mount it and set `LAYA_MODEL_PATH`. Hosts that cannot reach huggingface.co can bake weights from ModelScope (`MODELSCOPE_MODEL`). ARM64 CPU works natively; Apple Silicon runs the Linux ARM64 container on CPU (no MPS in Docker); DGX Spark inference is not yet reported.

## Checkpoint integrity
Off by default; two opt-ins.
- `revision=` pins a commit SHA, branch or tag; `PINNED_REVISIONS` holds reviewed SHAs; `LAYA_REVISION=reviewed` uses them. A default `Router` loads all three checkpoints from one bundle repo, so use `standalone_repos=True` with per-model pins, and pin all three.
- `expected_sha256={path: hex}` verifies files before parsing: list `rl_agent_config.json`, `tokenizer/tokenizer.json`, `encoder/config.json`, `model.safetensors`; leave out `tokenizer/tokenizer_config.json` (Laya may rewrite it). Generate the map yourself from a reviewed copy. Mismatch raises `ValueError`; a listed missing file `FileNotFoundError`. `LAYA_SHA256_DIGESTS` supplies it from the environment (flat applies to every checkpoint and is ignored if any `expected_sha256` reaches the Agent; nested is per checkpoint).
- Digests protect against upstream edits, corrupted downloads and tampered copies relative to what you reviewed. They do not make an unreviewed checkpoint trustworthy.
- Pinning is off by default so `HF_HUB_OFFLINE=1` offline caches keep working.

## Speed paths (optional, GPU-oriented)
- `compile=True` (`torch.compile`, dynamic shapes): warm-up compiles two graphs at load (tens of seconds each; about 120 s down to 50 s with `compile_cache=True`); no steady-state gain is reported; `reduce-overhead` mode serialises forwards process-wide.
- `fast=True` / `accelerate()`: TileLang kernels, CUDA only, fp32 not supported; TileLang CPU kernels exist but claim no speedup.
- AOTInductor `.pt2` package: needs CUDA PyTorch and a C++ compiler; 645 MB; load 0.45 s same process, 4.9 s fresh; bf16 decision logits differ from eager by up to 0.56 (argmax agreed on 7 of 7 rows).
- For a CPU-only intent service none of these matter; the baseline is 0.3 to 0.9 s per call.
