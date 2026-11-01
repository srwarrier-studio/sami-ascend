# Tasks: intent-api/02 training-data

- [x] 1. Floor and spend question: add "how much did we spend in october 2025?" (Purchase, `purchases_value`) and its near questions to the tuning set of `evals/questions.json`, set `DOMAIN_MIN_PROBABILITY` to 0.4 and re-run the evaluation. Done when: the numbers at the old and the new floor are recorded in the Laya notes.
- [ ] 2. Families and generator: `training/families.toml`, the generator with a fixed seed, typos and multi-clause combinations, the split by family, the calibration slice, `training build`. Done when: the same seed gives the same files and the tests for every rule pass.
- [ ] 3. Checks and Colab script: `training check` (counts, duplicates, overlap with the evaluation questions and the held-out families, token budget) and the Colab script and steps. Done when: the check passes on the generated set and the script is reviewed by the owner.
- [ ] 4. Train and measure: the owner trains on Colab; the tuned checkpoint is served as an extra checkpoint and compared with zero-shot, with the learning curve. Done when: the numbers are in the Laya notes and the owner decides to use the checkpoint or not.
- [ ] 5. Close-out: `notes.md`, roadmap and README entries. Done when: all tests pass and the phase is ready to merge.
