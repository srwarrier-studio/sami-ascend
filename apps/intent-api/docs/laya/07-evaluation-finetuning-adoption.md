# Evaluation, fine-tuning and adoption

## Evaluation harness (`laya-evals`, also `laya eval`)
Dataset: JSONL, one case per line; blank lines and `#` comments ignored.
| Field | Required | Meaning |
|---|---|---|
| `state` | yes | text or JSON |
| `questions` | yes | a Laya question dict |
| `expected` | yes | ground truth keyed by question id |
| `tags`, `language`, `model` | no | slicing; force a checkpoint per row |

Commands:
- `laya-evals validate <file>` format check, no model.
- `laya-evals run <data> --model ... --device ... [--min-accuracy X --max-ece X --score-within X] [--slice language|model|qid|tag] [--json F --markdown F]`
- `laya-evals compare <report> --baseline <file> --tolerance METRIC=VALUE` drift gate.
- `laya-evals agreement` student versus repeated teacher; `laya-evals evidence` inspects calibration artifacts without loading weights.
- Exit codes: 0 ok, 1 threshold or baseline failure, 2 usage error.
- Options: `--batch-size`, `--sort-by-length`, `--min-confidence T` (marks abstained, does not change scoring), `--revision [name=]SHA`, `--gate-policy gates.json` (per-slice rules), `--onnx PATH`, `--calibration PATH`.

Metrics: `choice_accuracy`, `noul_accuracy`, `score_mae`, `score_within_<tol>`, `ece` (15 bins), `brier`, `aurc`, `selective_accuracy@50/@80`, `mean_confidence`, `latency_p50/p95_ms`, `cost_per_decision_p50/p95_ms`. Confidence source preference: `answer_confidence`, then `confidence`, then derived; reports are comparable only when answers carry the same field. Ties at coverage cuts accept everything with the same confidence, so `selective_accuracy@50` and `aurc` can swing on tie-heavy data; a report records `coverage_metric_definition` and comparisons across definitions are refused. Reports record `dataset_sha256`, `questions_sha256`, `revisions`, thresholds.

Python helpers `evaluate_shortlist` and `evaluate_tournament` split errors into retrieval or elimination misses versus final-decision misses.

For our own harness: keep a held-out set that is only looked at at the end (the intent-api spec already says this), record the same identity facts, and report refusals separately from wrong answers.

## Fine-tuning (`laya-train` / `laya.train`)
Why: zero-shot base checkpoints are near chance on typed decisions (0.36 against 0.32 random); fine-tuned on 2,000 typed decisions it reaches 0.766 to 0.79. On MASSIVE intent, 0.73 to about 0.94. If zero-shot classification of our domains stays weak, fine-tuning on our own labelled questions is the documented route.

Data:
- CSV: one row per decision, a text column and a label column; the label becomes a `choice` over its distinct values (first-appearance order). Excel BOM is handled.
- JSONL: `{"state", "questions", "expected"}` (a label, true/false for noul, a level for score) or `gold` (teacher probabilities). Mixed shapes allowed.
- `laya-train --data tickets.csv --text-column body --label-column department --dry-run` reports counts, skip reasons (`empty_text`, `empty_label`, `invalid_question`, `invalid_target`, `options_collapsed`, `options_beyond_max_len`) and the optimizer budget.
- Train: `laya-train --data ... --base english --out ./checkpoint`; load with `laya.load("./checkpoint")` plus the saved `questions.json`. Python: `finetune(data, "english", out, TrainConfig(loss="soft-ce", shuffle_options=("choice",)))`.

Defaults: 4 epochs, micro-batch 8, grad-accum 8 (effective 64), encoder LR 2.5e-5, head LR 1e-4, grad clip 1.0, loss `rlcd`, seed 0, calibration slice up to 400 items or 10%. `updates = epochs * ceil(ceil(items / micro_batch) / grad_accum)`; small datasets get few updates, so raise epochs. `--shuffle-options` re-orders choices each epoch (mainly for many-option questions). `--freeze-encoder` trains the head only (fits small GPUs and CPU but gains much less). Hardware: CUDA, MPS or CPU; GTX 16xx needs `amp=False`.

Reference results (typed-decisions, 2,000 decisions, one seed): base 0.362 accuracy (ECE 0.174); rlcd 0.7715; soft-ce 0.790; soft-ce with shuffle 0.7875. Answers that flip when options are reversed: 0.357 base, 0.062 to 0.078 fine-tuned.

Calibration inside training: a held-out slice is removed before training, one temperature per question type is fitted by LBFGS (clamped to [0.1, 10]); under 10 items the temperature stays 1.0 and the report warns. Ship `rl_agent_config.json` with the weights, and make sure no stale `temperature_by_options` survives a copy (it silently masks the new fit).

Diagnostics for a run stuck at chance: prepend the label as text (`label=<x>;`) as a positive control; one seed is not conclusive (9 of 15 identical runs left the plateau).

Cautions: targets set the ceiling; the calibration slice is small, so keep separate evaluation data; labels must fit choice/score/noul; high option counts degrade (#394); negation can carry over (#377).

A separate page (browser agent) shows the same recipe on a harder task: input format can matter more than data volume (truncation hid candidates until they were moved into the option list), templated labels leak shortcuts, negatives should match deployment, rare classes need reweighting, a stronger teacher is not automatically better, and live results have run-to-run variance larger than small model differences.

## Staged adoption (the docs' rollout advice)
Laya returns a decision, not permission to act. The application owns the incumbent action, eligibility, thresholds, review, fallback and rollback.
1. **Shadow:** run on real traffic while the incumbent stays authoritative. Log `run_id`, schema, answer, probabilities, confidence, checkpoint, incumbent action, eventual outcome, latency, errors. Logging must be side-effect free and redacted.
2. **Compare:** disagreement is a prompt for review, not an error. Keep an explicit unknown/review bucket; slice by checkpoint, language, schema, action type; report coverage and disagreement with accuracy.
3. **Choose a policy from held-out evidence:** threshold is an application choice; record checkpoint, schema version, calibration method, threshold, evaluation set and owner; re-evaluate when any change. Confidence orders decisions, it does not establish correctness. Test attacker-influenced text with paired clean/instructed cases.
4. **Promote a bounded slice:** only for evaluated checkpoint/language/schema, reversible or reviewed actions, with a traffic cap, sampling and a named rollback condition.

For intent-api this is a direct fit: the answer step is deterministic and already refuses; Laya picks only the scenario, and every Laya decision can be shadow-logged and compared against the rules matcher before it is trusted.
