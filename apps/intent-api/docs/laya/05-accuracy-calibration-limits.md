# Accuracy, calibration and known limits

## Numbers the docs state
- `laya-typed-decisions`: 0.766 accuracy against a 0.461 majority-class baseline, on the benchmark it was fine-tuned on. Both base checkpoints score below that baseline zero-shot (about 0.36 and 0.35 against 0.318 random). This supports fine-tuning for a similar task; it does not show accuracy on a new domain with an untrained checkpoint.
- Banking77 (77 labels) performs poorly at the default token budget.
- MASSIVE intent (English, 20 options): fine-tuning raised accuracy from 0.730 to about 0.94.
- Latency (docs): about 33 to 40 ms on a Tesla T4, p50 about 126 ms on Apple silicon, 193 to 464 ms on CPU (one page also says 88 to 464). Our measurement on CPU: about 0.3 s for a short question, 0.6 to 0.9 s for a multi-part one; model load about 5 s.
- Long text: less reliable beyond about 4,000 preceding tokens (irrelevant for questions).
- Third-party comparison figures (Jev etc.) come from different prompts and sample sizes, not a controlled test.

## Known limits (from the docs)
- **Many options:** keep a single choice question to roughly 20 options. Option descriptions share a fixed token budget; past about 40 the default budget collapses accuracy. Widening `head_max_len` (and `max_len`) helps but can hurt smaller sets; measure. Use `predict_shortlist` or `predict_tournament` for big label sets.
- **Option order matters:** it can change a `choice` answer. Fine-tuning with `--shuffle-options` lowers this (answers changing when reversed: 0.357 base, 0.062 to 0.078 fine-tuned).
- **Negation:** forced-choice questions can return the wrong label for negated states with high confidence (issue #377). Wording of boolean labels can fail: a `noul` asking whether something is "positive" can answer no for every state at confidence 1.0; setting `labels` can fix it (issue #1244).
- **`noul` can follow its labels** instead of the state; validate any relabelling.
- **`score` is the weakest primitive** in the English suites; the multilingual checkpoint shows a bias against the first level.
- **Held-out moderation is weak** in the application benchmark.
- **Language:** the English checkpoint can be confidently wrong outside English; use `Router`.
- **Latency does not transfer:** T4 numbers do not predict CPU or cold-load times.

## Calibration
- Confidence is not calibrated as shipped. Both base checkpoints are over-confident on the published suites (a separate routing task was under-confident). `laya-multilingual` ships with no fitted temperatures; loading prints a warning that `choice:11+` is clamped to 0.5 (we saw it).
- Set thresholds only from held-out data of your own workflow, per checkpoint and per question shape. No universal threshold exists.
- `answer_confidence` is what temperature scaling fits; `min_confidence` gates on it.
- Fitting: `agent.fit_temperatures(records)`, `fit_binning`, `save_calibration`, `load_calibration`; helper `laya.calibrate.records_from_labeled`; `fit_abstention_thresholds(records, temperature, temperature_by_options, target_error=0.1)` gives a per-bucket threshold map that `min_confidence` accepts. Buckets with fewer than 10 items are omitted.
- Temperature scaling changes confidence only, never the argmax or accuracy. A confident wrong answer stays confident wrong; calibration lowers its confidence on average, it does not remove it.
- Metrics to read: ECE (15 bins, lower is better), Brier, AURC, `selective_accuracy@50/@80` (accuracy on the most confident half or 80%).

## Guardrail limits (relevant to any "is this about our business" gate)
Issue #781, 53 synthetic cases, reporter's figures: the guard presets catch direct attacks but miss instructions embedded in document-shaped text (prompt-injection scores 0.18, 0.30, 0.00 on three embedded cases, below 0.5). A benign passage quoting an attack phrase scored 0.619 and was blocked: the head responds to vocabulary, not to whether text addresses the model. Rates at threshold 0.5: recall 0.72, false positive rate 0.21. Lowering the threshold to 0.15 blocked 9 of 28 should-allow cases. Lesson that carries over: a low score is not "safe", a high score is not "right", and a vocabulary-driven head can be fooled in both directions. `harm_severity` is a `score` (expected level 0..3), not a probability.

## How to interpret a benchmark
Accuracy needs a baseline and a data split; confidence is separate from accuracy (ECE does not set a safe threshold for another task); check whether the data was in training. For our deployment: hold out one set of questions with expected answers, use it for every checkpoint and wording compared, record checkpoint revision, versions, device, question count, option count and token budget, include a simple baseline, and report warm latency separately from cold load.
