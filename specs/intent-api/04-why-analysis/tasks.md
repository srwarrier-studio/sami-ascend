# Tasks: intent-api/04 why-analysis

- [x] 1. The graph: `graph.toml`, loader, `graph check` and `graph show` moved in with their tests and the maintenance doc. Done when the graph tests pass and `graph check` passes against the synapse-api registry.
- [x] 2. The analysis: walk engine, `AnalyseQuestion`, anomaly kinds, scoring and wording moved in, with the data port on `SynapseMetricSource` (records read, `company`, currency choice). Done when the moved analysis tests and the currency and company cases pass on the mock source.
- [x] 3. The `why` response: `answers.toml` entries, the blocks and sentences, the `company` on the request, the refusals. Done when the answer cases pass through `POST /v1/intent/answer`.
- [x] 4. `why-eval` and the 13 scenario evaluations for `sabinsa` and `USD`. Done when every scenario passes and the group, INR and not-allowed cases pass.
- [ ] 5. Close-out: README, notes, roadmap, settings, `dev.sh` note. Done when all intent-api tests pass and the phase is ready to merge with the others.
