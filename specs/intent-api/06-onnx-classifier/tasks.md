# Tasks

- [x] 1. Contract and harness: read what intent-api needs from the response, write a small script that scores any server or local model on `heldout.jsonl` (accuracy, ECE, latency, RAM). Done: Laya's 91.85% and ECE 0.0527 reproduced.
- [ ] 2. Baselines A and B on the host with the harness. Done when both have numbers next to Laya's and the bar is judged.
- [ ] 3. Colab notebook for the cross-encoder (DistilBERT first), owner runs it and downloads the checkpoint. Done when the checkpoint is in a local untracked folder.
- [ ] 4. Export to ONNX, int8, temperature calibration, harness numbers. Done when accuracy, ECE, latency and RAM are measured.
- [ ] 5. FastAPI server with the Laya-compatible endpoint and its own service in compose, switched by `LAYA_URL`. Done when `intent-api eval` runs against it and stopping it gives `cannot_classify_now`.
- [ ] 6. Comparison write-up and decision notes in `specs/notes.md`.
