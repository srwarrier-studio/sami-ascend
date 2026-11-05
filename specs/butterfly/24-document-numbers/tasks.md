# Tasks

- [x] 1. `NumberRange` in the domain with the five families, tests for next, skip, full, year restart. Done when the new tests pass and nothing else changes.
- [x] 2. The ALPHA helper and the standard sales order services (V2 and V4): numbers shown without leading zeros and accepted in either form in keys, filters and `$apply` groups. Done when the helper tests and the sales order standard tests pass.
- [x] 3. The standard business partner service and the standard requisition service: customers, suppliers and references converted the same way. Done when their tests pass.
- [x] 4. Consumers: workspace-api pads the customer number it sends to the custom create; the tests of workspace-api that compare standard numbers are updated. Done when the workspace-api, synapse-api and intent-api suites pass.
- [ ] 5. The next requisition and sales order numbers come from `NumberRange`; notes: `specs/notes.md` and `docs/sap/document-numbers.md` mark what is done and open [verify] items go to `docs/sap/consultant-questions.md`. Done when the butterfly suite passes and no padded standard number remains in those docs.
