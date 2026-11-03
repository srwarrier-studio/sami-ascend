# Tasks

- [ ] 1. Schema, connection and seeding. Done when the tables exist, the seeds load into them, and a restart with the same settings keeps the data.
- [ ] 2. SQLite repositories for orders, master data and drivers, with writes that persist. Done when the existing repository-level tests pass on both implementations and an order survives a restart.
- [ ] 3. Query push-down. Done when `$filter`, `$orderby`, `$top`, `$skip`, `$count`, `$select`, `$expand` run as SQL, the injection case passes and the parser tests are unchanged.
- [ ] 4. Summaries as views and receivables as parameter queries, with the statements in `docs/sap/views/`. Done when the summary and receivables tests pass and a view equals a hand total.
- [ ] 5. Make it the default, update the README and `docs/sap/`, measure the 1,000-row read. Done when all 947 existing tests pass on SQLite and the README explains `BUTTERFLY_DB`.
