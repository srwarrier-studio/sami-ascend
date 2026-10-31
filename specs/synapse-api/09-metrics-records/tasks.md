# Tasks

- [x] 1. The registry: its dataclasses, the loader with checks, and the shipped `registry.toml` for the three sales metrics dimensions and the four drivers record types. Done when the load, check-failure and listing cases pass.
- [x] 2. One shared OData reader, the sales source rebuilt on it, and registry-driven metric reads. Done when the sales paging and request tests still pass and a test-registry metric reads.
- [x] 3. `/metrics`, `/metrics/{metric}/compare` and `/month`, moved from phase 08 and made generic, and the old routes removed. Done when phase 08's cases pass on the new routes and the unknown-metric cases pass.
- [ ] 4. The records use case and `/records` with `/records/types`. Done when the interval, delay, key, invalid, role, cache and 503 cases pass against the mock.
- [ ] 5. The butterfly scenario checks, notes and roadmap. Done when the contract, delivery, production, component and breakdown cases pass through butterfly.
