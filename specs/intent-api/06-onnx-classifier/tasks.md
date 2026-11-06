# Tasks

- [x] 1. Contract and harness: read what intent-api needs from the response, write a small script that scores any server or local model on `heldout.jsonl` (accuracy, ECE, latency, RAM). Done: Laya's 91.85% and ECE 0.0527 reproduced.
- [x] 2. Baselines A and B on the host with the harness. Done when both have numbers next to Laya's and the bar is judged. Result: TF-IDF 76.4%, bge-small zero-shot 56.8%, bge-small + logreg 82.1% (bar not met).
- [x] 3. Colab notebook for the cross-encoder (DistilBERT first), owner runs it and downloads the checkpoint. Result: DeBERTa-v3-small on the widened families, 92.97% on the old held-out, 92.77% on the new one (Laya 91.85%).
- [x] 4. Export to ONNX, int8, temperature calibration, harness numbers. Result: weight-only int8 matmuls plus int8 embeddings, `w8e.onnx` 179 MB, 92.77% accuracy, ECE 0.0255, p50 289 ms at 2 threads; default dynamic int8 lost 12 to 14 points and was rejected.
- [ ] 5. FastAPI server with the Laya-compatible endpoint and its own service in compose, switched by `LAYA_URL`. Done when `intent-api eval` runs against it and stopping it gives `cannot_classify_now`.
- [ ] 6. Comparison write-up and decision notes in `specs/notes.md`.
