# intent-api/02 training-data

## Goal
A fine-tuned Laya checkpoint that reads managers' questions into domains and scenarios better than the zero-shot one, trained from a deliberately designed set of invented questions on Google Colab, and measured with the existing evaluation. Nothing about the app's behavior changes except which checkpoint it asks.

## Why
Phase 01 measured the zero-shot reading on questions we wrote: 79% of held-out answerable questions exactly right, 15% wrong answers where a refusal or another scenario was right (`apps/intent-api/docs/laya/09-intent-api-notes.md`). The misses are about wording, not rules: comparison phrasing ("up or down against", "relative to"), generic money questions ("how much did we spend" read as Sales at 0.26), misspellings, forecasts that look like figures. The Laya docs report fine-tuning moving similar tasks from about 0.36 to 0.77 (typed decisions) and 0.73 to 0.94 (intent classification), with far fewer answers flipping when the options are reordered (`docs/laya/07`).

## Rules for the training data
- Invented only. Management does not allow company data (names, figures, real manager questions) to go to AI, and Colab is Google's cloud, so nothing from the company goes into the training set, the notebook or the Colab session. Real manager questions, if used, stay on the owner's machine and are used only to test locally.
- Train on patterns, not on every possible question. The number of possible questions is in the thousands because slots (periods, customers, materials, countries) multiply every phrasing, but the model needs variety of phrasing, not every combination. The set is built from families: one family is one meaning (a domain, or a domain and a scenario) with many different ways to say it (templates and paraphrases) and invented names and periods dropped into the slots. A cap per family and per template keeps one phrasing from dominating. A learning-curve check (train on 25%, 50%, 100%) says when more data stops helping.
- Same format as production. Each item is what the app sends: `state` `{"question": text}`, the same instructions, the same short option descriptions, one question per item (the domain question; the scenario question for one clause), with the expected answer. Option order is shuffled and sometimes only some scenarios are offered, so a new `[[scenario]]` in `scenarios.toml` still works without retraining.
- Hard cases on purpose: near pairs (spend and earn, imports and exports, compare and trend, versus last month and versus last year), forecasts and margins labelled as refusals, not-business questions labelled `Other`, multi-clause questions with each clause labelled, and misspellings and shorthand added by a controlled generator.
- Honest splits. The 113 questions in `evals/questions.json` are never in training. Training families and test families are different (split by family, not by random question), so a rephrasing of a training question is never a test question. A calibration slice is held out of training, as the docs require. A new held-out set is written for this phase because the old one is spent.

## Behavior
- `apps/intent-api/training/`: `families.toml` (the families), a generator (`intent-api training build`) that expands them with a fixed seed into JSONL files for `laya-train` (domain items, scenario items, a held-out family set and a calibration slice), `intent-api training check` (counts per domain, scenario and family, duplicates, items that do not fit the token budget, the same checks as `laya-train --dry-run`), and a Colab script with the steps to train and download the checkpoint. The generator and the checks run on the host; only the training runs on Colab.
- The tuned checkpoint is loaded by `laya-serve` as an extra checkpoint (`LAYA_EXTRA_MODELS` or `LAYA_MODEL_PATH`) and chosen with `LAYA_MODEL`; the app code does not change.
- `intent-api eval` compares checkpoints on the same questions, and reports the learning curve results when asked.

## Acceptance cases
- `training build` gives the same files for the same seed; `training check` passes and reports no question shared between the training and the held-out families, nor with `evals/questions.json`.
- Every scenario of the library and every domain appears in many families; the refusal and `Other` families are at least a fifth of the set.
- Adding a `[[scenario]]` to `scenarios.toml` and a family for it needs no code change.
- The tuned checkpoint is compared with the zero-shot one on the new held-out set, on the tuning questions of `evals/questions.json` and on a local set written by the owner. The bar: exactly right on at least 90% of answerable questions and wrong answers on at most 5% of questions, with the floors chosen on the tuning set only.
- No file in the training folder contains a real name, figure or manager question.

## Out of scope
Slots, answers, the web app, Docker, training on real company data, training anywhere but Colab, a model other than Laya, changing the app's rules.

## Depends on
`intent-api/01` (merged). The owner trains on Google Colab (GPU) and returns the checkpoint folder.

## Open items for the owner
1. Which GPU does Colab give (T4 is enough per the docs, about 4 to 6 minutes for 6,000 decisions on 2xT4) and is a paid plan available?
2. The owner's local set of real-sounding questions: how many, written by whom, and kept where (never in the repo)?
3. The domain floor and the spend question (task 1) are small and come first.
