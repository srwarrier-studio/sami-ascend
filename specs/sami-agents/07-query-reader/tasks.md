# Tasks: sami-agents/07 query-reader

- [ ] 1. Model measurement: schema task and `query-eval` question set for candidate models. Done when: accuracy and speed per model are in `notes.md` and a model is chosen with the owner.
- [ ] 2. Query and checks: `Plan` and `Query` entities (step cap, shared period), validation against the registry, capabilities text for the prompt. Done when: each invalid case is rejected with a clear error, tested.
- [ ] 3. Reading: entity linker, period rules, model gateway with schema, retry once, clarify. Done when: the entity, period and retry acceptance cases pass with a mock model.
- [ ] 4. Execution: `QueryExecutor` with filters, split, rank and other periods; the `unanswered` log and command. Done when: the answering acceptance cases pass on mock data.
- [ ] 5. Evaluation, web and notes: `query-eval` with the real questions and held-out run, the small synapse-web change, notes and roadmap. Done when: results with limits are in `notes.md` and tests pass.
