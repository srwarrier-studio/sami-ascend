# onnx-classifier

Answers the choice questions intent-api asks (`POST /v1/systemone`, the same request and response as Laya) with a fine-tuned DeBERTa-v3-small cross-encoder on ONNX Runtime. Each option is scored against the question with one logit; the answer is a temperature-calibrated softmax over the offered options. No torch.

## Run
Compose runs it by default (`docker compose up -d --wait intent-api` starts it; port `127.0.0.1:8012`). The model folder `Training/classifier-model/` (git-ignored: `model.onnx`, `w8e.onnx.data`, tokenizer files, `calibration.json`) is mounted read-only.

On the host: `MODEL_DIR=Training/classifier-model PORT=8012 uv run --project apps/onnx-classifier onnx-classifier`.

Settings: `MODEL_DIR`, `THREADS` (default 2), `API_KEY` (optional bearer token), `PORT`.

## Test
`uv run --project apps/onnx-classifier --with pytest python -m pytest apps/onnx-classifier` (the real-model test is skipped when `Training/classifier-model` is missing).

## A new model
Train on Colab with `apps/onnx-classifier/tools/cross-encoder.ipynb`, unzip the fp32 export, then on the laptop: `weight_only.py` (8-bit weights) and `embedding_quantize.py` (8-bit embeddings) in `apps/onnx-classifier/tools/`, copy the result into `Training/classifier-model/` with `calibration.json`, and restart the service. Default dynamic int8 quantization loses 12 to 14 points on this model; do not use it.

## Tools
`tools/`: the Colab notebook, `weight_only.py` and `embedding_quantize.py` (quantization), `onnx_scorer.py` and `bench.py` (accuracy, ECE, latency on `Training/out/heldout.jsonl`), `parallel_requests.py` (parallel requests against a running server). Run them with `uv run --package intent-api python apps/onnx-classifier/tools/bench.py <url>`; the quantization scripts need `onnx`, `onnxruntime` and `onnx_ir` in a scratch environment.
