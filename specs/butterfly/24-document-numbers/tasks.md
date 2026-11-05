# Tasks

- [x] 1. `NumberRange` in the domain with the five families, tests for next, skip, full, year restart. Done when the new tests pass and nothing else changes.
- [ ] 2. Requisition, sales order and material document numbering use `NumberRange`; sales orders, customers and suppliers become canonical unpadded strings in the sample data; keys and filters accept leading zeros. Done when the butterfly suite passes.
- [ ] 3. Consumers: update the padded sample numbers in the workspace-api, workspace-web, synapse-api and intent-api tests. Done when each suite passes (the one known workspace-api failure excepted).
- [ ] 4. Notes: `specs/notes.md` and `docs/sap/document-numbers.md` mark what is done; open [verify] items go to `docs/sap/consultant-questions.md`. Done when no padded number remains in the docs.
