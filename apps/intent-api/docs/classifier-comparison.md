# Classifier comparison: Laya and onnx-classifier

Measured 2026-11-06 and 2026-11-07 with `intent-api eval --final` (domain threshold 0.40, scenario threshold 0.30) and `apps/onnx-classifier/tools/bench.py`. Laya is `sap-intent-v2` (ModernBERT-large, `laya-serve`, CPU torch); the new one is DeBERTa-v3-small on ONNX Runtime with 8-bit weights and embeddings (`apps/onnx-classifier`).

## Questions in `evals/questions.json`
87 tuning questions (written earlier, thresholds were chosen on them) and 139 held-out questions (34 earlier ones, 105 seeded from the owner's nine). The assistant wrote all of them apart from the nine seeds.

| | Laya | onnx-classifier |
|---|---|---|
| Tuning: answerable exactly right (of 56) | 51 | 47 |
| Tuning: harmful answers | 1 | 1 |
| Tuning: domain right (of 87) | 85 | 84 |
| Held-out: answerable exactly right (of 82) | 73 | 77 |
| Held-out: refusals correct (of 57) | 54 | 57 |
| Held-out: harmful answers | 4 | 2 |
| Held-out: domain right (of 139) | 127 | 134 |
| Both sets: exactly right (of 138) | 124 | 124 |
| Both sets: harmful answers | 5 | 3 |
| Both sets: domain right (of 226) | 212 | 218 |

Laya answered three DSO-style Finance questions ("whats our dso", "days sales outstanding this quarter", "whats our daily sales outstanding") with a sales figure; the new one refuses them.

## Generated held-out set (`Training/out/heldout.jsonl`, 1,297 items, a different set each round)
Round 3 of the new model: 93.71% accuracy, ECE 0.031. Laya on the earlier held-out set: 91.85%, ECE 0.0527. The sets differ, so these two numbers are not a like-for-like comparison.

## Cost
| | Laya | onnx-classifier |
|---|---|---|
| Memory | 8.8 GB | 290 MB idle, 330 MB under load |
| Image | 1.8 GB | 402 MB |
| Time per call (p50 / p95) | 703 / 1,091 ms on 4 cores | 300 / 395 ms on 2 threads |
| Time per question in `intent-api eval` | 1.4 to 1.6 s | 0.55 to 0.61 s |
| Capacity | not measured | about 5 calls per second per container (2 cores), 1.4 calls per question |

## Caveats
Laya leads on the 87 tuning questions (51 against 47). The held-out lead of the new model is partly earned: Finance, Inventory and Production jargon families were added after the first round failed on those questions. Real questions from `unanswered.jsonl` should decide it later. Quantizing the model with default dynamic int8 loses 12 to 14 points; only weight-only 8-bit is used (see `specs/notes.md`).
