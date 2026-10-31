# Tasks: sami-agents/07 scenario-library

- [ ] 1. Gate measurement: scenario-eval question set (single, multi-part, real) and a Laya per-scenario relevance test at several thresholds. Done when: wrong, extra and refused counts per threshold are in `notes.md` and the threshold and the category step are chosen with the owner.
- [ ] 2. Library and checks: `scenarios.toml` loader, `Scenario` entity, `scenarios check` and `show`, the two existing scenarios moved in, `docs/scenarios-maintenance.md`. Done when: bad files fail with a clear message and each check has a test.
- [ ] 3. Matching: category and scenario passes over `CaseModel`, gate, `covers`, `MAX_SCENARIOS`, `cannot_answer` with nearest scenarios and the `unanswered` log and command. Done when: the matching acceptance cases pass with a mock model.
- [ ] 4. Slots and answers: entity linker, shared period and numbers, clarify, the joined answer with "how I read it", optional period fallback. Done when: the entity, multi-part and clarify acceptance cases pass on mock data.
- [ ] 5. Evaluation, web and notes: held-out run, the small synapse-web change, notes and roadmap. Done when: results with limits are in `notes.md` and tests pass.
