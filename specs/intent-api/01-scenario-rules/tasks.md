# Tasks: intent-api/01 scenario-rules

- [x] 1. App scaffold: `apps/intent-api` as a `uv` workspace member, folders, settings, app factory, `GET /health`, the cookie check, README, `tech-stack.md` line. Done when: the app starts on 8006, health answers and tests pass.
- [ ] 2. Scenario library: `Scenario` entity, `scenarios.toml` loader with all the rejections, the 16 draft scenarios with words and examples, `scenarios check` and `show`. Done when: every rejection has a test and the shipped file passes `check`.
- [ ] 3. Matcher: normalise, stems, typo matching, category, scoring, `covers`, `MAX_SCENARIOS`, `cannot_answer` with nearest choices and the `unanswered` log and command, `POST /v1/intent/match` with `why_matched`. Done when: the acceptance cases for matching pass.
- [ ] 4. Evaluation: `evals/questions.json` from `reference/` with a held-out part set aside, `intent-api eval` with the threshold sweep. Done when: the numbers print and the threshold is chosen with the owner.
- [ ] 5. Close-out: `notes.md` with results and limits (against the Laya test), roadmap and README entries. Done when: all tests pass and the phase is ready to merge.
