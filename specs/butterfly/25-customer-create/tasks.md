# Tasks

- [x] 1. Model and store: the new `Customer` fields with defaults, `CUSTOMER` number range, `add_customer` in both repos, older database rebuilt. Done when the existing butterfly suite passes unchanged.
- [ ] 2. Read sets: `A_BusinessPartner`, `A_BusinessPartnerAddress` and the role set from the saved definition, filled from the customer. Done when the read samples still pass and the new sets answer.
- [ ] 3. Create: `POST A_BusinessPartner` deep insert, number from the range, all-or-nothing save. Done when the happy path and number cases pass.
- [ ] 4. SAP-style refusals and the live check: every refusal case, new customer in the dropdown and in a sales order, short note for the consultants. Done when the acceptance cases pass.
