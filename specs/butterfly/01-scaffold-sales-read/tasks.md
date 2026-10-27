# Tasks

- [x] 1. Scaffold `apps/butterfly` with entities, `SalesOrderRepo`, seed builder, and plain `GET SalesOrder` / `SalesOrder('key')` with the error format and logging. Done when list, single, 404 and 500 cases pass.
- [x] 2. `$filter` parser and evaluator. Done when every operator, function, precedence and bad-filter case passes.
- [ ] 3. `$select`, `$orderby`, `$top`, `$skip`, `$count` and the unsupported-option 400s. Done when the query option cases pass.
- [ ] 4. `$expand=_Item` and `SalesOrder('key')/_Item`. Done when the expand cases pass.
- [ ] 5. Contract check: tests compare responses with the field tables in `docs/sap/sales-contract.md`, plus a run command in the app README. Done when the contract example cases pass.
