# Tasks

- [ ] 1. Domain records, a `DriversSource` interface with a mock, and the `ReadRecords` use case (types, key fields, validation, window overlap, `delay_days`). Done when the interval, delay, ordering and invalid cases pass against the mock.
- [ ] 2. One shared OData reader for paging, request id and errors, and `ButterflyDriversSource` with its mapper and the base URL setting. Done when the drivers requests, mapping and failure cases pass and the sales paging tests still pass.
- [ ] 3. The `/records` route, schemas, roles and cache. Done when the route, role, cache, invalid and 503 cases pass.
- [ ] 4. Butterfly scenario checks (`august-contract`, `breakdown-shortfall`), notes and the roadmap rename. Done when the four scenario cases pass.
