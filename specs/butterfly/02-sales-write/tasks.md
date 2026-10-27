# Tasks

- [x] 1. Contract first: add `FIELD_INVALID`, `FIELD_NOT_ALLOWED` and `INVALID_REQUEST_BODY` with examples, and the "SAP fills in" and etag-always-changes rules, to `docs/sap/sales-contract.md`. Done when `docs/sap` tests pass and the three codes each have an example.
- [x] 2. Master data, repo `add` and `update`, and the `CreateSalesOrder` use case with every validation rule, including `FIELD_INVALID` and `FIELD_NOT_ALLOWED`. Done when every create validation case passes at use-case level.
- [ ] 3. `POST SalesOrder`: reading the JSON body, `INVALID_REQUEST_BODY`, `VALIDATION_FAILED` response, `201` and `Location`. Done when the create acceptance cases pass over HTTP.
- [ ] 4. `ChangeSalesOrder` use case and `PATCH SalesOrder('key')` with `If-Match`, 412, 428. Done when the PATCH acceptance cases pass.
- [ ] 5. Contract tests for the write examples, and README update. Done when `test_contract.py` replays the POST, 400 and 412 examples.
