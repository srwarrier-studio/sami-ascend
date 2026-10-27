# Tasks

- [x] 1. Contract check first: confirm the three tables and example in `docs/sap/sales-contract.md` (note cancelled orders are excluded, no read by key), add the consultant question. Done when `docs/sap` tests pass.
- [x] 2. Summary use cases (`SummarizeByDay`, `SummarizeByCustomer`, `SummarizeByMaterial`) over `SalesOrderRepo`, with `Decimal` sums and cancelled exclusion. Done when the grouping and total acceptance cases pass at use-case level.
- [x] 3. Field tables, JSON mappers and the three GET routes using `apply_list_query`. Done when the query option and error acceptance cases pass over HTTP.
- [x] 4. Contract test un-skip, create-then-read test, README and notes update. Done when `test_contract.py` runs the summary example and a POST changes today's rows.
