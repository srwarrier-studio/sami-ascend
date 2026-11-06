# intent-api/06 onnx-classifier

## Goal
An experiment: a small own classifier server (FastAPI + ONNX Runtime, no torch) that answers the same `POST /v1/systemone` choice requests as Laya, so `intent-api` can switch with `LAYA_URL`. Laya and `infra/classifier` stay untouched and remain the way back.

## Why
Laya (ModernBERT-large, `Training/sap-intent-v2`) needs about 4.5 GB RAM per replica; two replicas plus the stack crashed the laptop on 2026-11-06. Held-out accuracy is 91.85%. Target here: under 2 GB RAM, an image without torch, and a model we can train and change ourselves. Porting Laya itself was rejected (no export script, `laya.common` imports torch).

## What the server must do
- Same contract as `LayaChoiceClassifier`: request `state.question`, `questions.choice.criteria` (option name to short description) and `instructions`; answer `answers.choice.probabilities` for exactly the offered options. Nothing else of Laya's API is used. Policy (thresholds, `Other`, refusals) stays in intent-api.
- Options are dynamic (scenarios are added in `scenarios.toml` and only some are offered per call), so a fixed-label head does not fit. The model scores each pair (question, option name and description) with one logit; probabilities are a softmax over the offered options, temperature-calibrated on the calibration slice.
- Trained from the existing `Training/train.jsonl` (same items, no new data), evaluated on `Training/heldout.jsonl`. Training happens on Colab only; export, int8 quantization and serving run on the host.

## Candidates, in order
1. Baseline A: TF-IDF + linear model on pairs. Baseline B: small sentence-embedding model (bge-small) with cosine plus calibration. Both run on the host in minutes and set the floor.
2. Cross-encoder fine-tuned on Colab: DistilBERT first (smallest and fastest), DeBERTa-v3-small if it misses the bar, ModernBERT-base last. Exported with optimum to ONNX, int8.
Stop at the first candidate that meets the bar.

## Hosting
The services will run on AWS, so the target is a small CPU task, not a big instance. Latency and RAM are measured pinned to 2 vCPU in a container limited to 2 GB, and the image is built for amd64 and arm64 (Graviton). No GPU.

## Laya reference (measured 2026-11-06, `Training/experiments/bench.py`, 4 cores)
Accuracy 91.85%, ECE 0.0527, p50 703 ms, p95 1,091 ms, server RAM 8.8 GB.

## Acceptance cases
- Held-out accuracy at least 90% on `heldout.jsonl` (Laya: 91.85%), with expected calibration error reported next to Laya's.
- `intent-api eval` with the new server gives the same or better exactly-right and wrong-answer rates as with Laya on `evals/questions.json`.
- Peak RAM under 2 GB at 2 vCPU; p95 latency per request reported next to Laya's; image size reported.
- Switching is only `LAYA_URL` (and key/model if needed); stopping the server still gives `cannot_classify_now`; Laya service and `infra/classifier` have no diff.
- Result written to `apps/intent-api/docs/` as a short comparison table, honest if Laya wins.

## Out of scope
Changing intent-api rules, new training data, replacing Laya in compose, GPU, training on the laptop, real company data (invented data only).

## Depends on
intent-api 02, shared 18.
