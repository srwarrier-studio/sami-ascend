# Tasks

- [ ] 1. Model and store: order header kept next to the stored items, `PURCHASE_ORDER` number range, repository methods to add an order and cancel an item, in memory and SQLite, summaries unchanged. Done when the existing suite passes and the new repository tests pass.
- [ ] 2. Read service: real `$metadata`, `PurchaseOrder`, `PurchaseOrderItem`, schedule lines, query options, errors. Done when the row contract test against the saved sample passes.
- [ ] 3. Create use case and `POST PurchaseOrder`: validation, refusals, requisition item linking, idempotency. Done when the refusal cases and the create case pass.
- [ ] 4. Item delete (`PATCH` with deletion code and `If-Match`) and the synapse effect. Done when the summaries rise on create and fall on delete in a test through the summary routes.
- [ ] 5. Consultant questions, `notes.md` (orders created released), README of the service, roadmap line.
