# butterfly/24 document-numbers

## Goal
Butterfly numbers its documents and master records the way SAP does (families, year dependence, item steps, and numbers without leading zeros as the real services print them), so the next P2P documents and every consumer see the same strings that SAP will give.

## Why
`docs/sap/document-numbers.md` compared butterfly with the sandbox samples. Requisition and material document numbers already match. Sales orders, customers and suppliers are padded to ten digits (`0000100001`) but the real services return `43103`, `17100001`, `17300001`. The purchase order, goods receipt, invoice and payment phases each need a number range and would otherwise invent their own.

## Behavior
- **`NumberRange`** (domain): a start, an end and a `next(taken)` that returns a higher number than any taken, never reusing one; raises when the interval is full. One instance per family: purchase requisition (from `10000000`), purchase order (`4500000000` to `4599999999`), material document (`4900000000` upward, per year), supplier invoice (`5100000000` upward, per fiscal year), sales order. Year dependent families take the year and restart per year; accounting documents take company code and year.
- **Strings as SAP prints them:** sales orders, customers and suppliers are returned without leading zeros. Sample numbers become 8 digits like the sandbox (`10000001` for the first Sabinsa customer, `20000001` for the first supplier, sales orders `20001` and up), kept as one canonical string.
- **Input:** a key or filter value with leading zeros (`0000043103`) finds the same record (SAP's conversion on input). Output is always the canonical string.
- **Items:** requisition, order and sales order items count in steps of 10 (existing behavior stays); material document and invoice items count 1, 2, 3.
- **Gaps:** a number is never reused; the mock does not promise gapless numbers.
- **Consumers:** workspace-api, workspace-web, synapse-api and intent-api tests that hold the old padded numbers are updated to the new samples, with no change to their code unless a test shows they depend on the padding.

## Acceptance cases
- `NumberRange` gives increasing numbers, skips taken ones, never repeats, and refuses when full; year dependent ranges restart per year.
- Sales order, customer and supplier numbers in every butterfly service have no leading zeros; a request with leading zeros returns the same record.
- Requisition numbers still start at `10000000`; material documents still show `49…` with `MaterialDocumentYear`.
- A sales order created through the standard service gets the next number of its range and appears in lists and by key in the canonical form.
- The whole butterfly suite, and the suites of workspace-api, workspace-web, synapse-api and intent-api, pass.

## Out of scope
Purchase order, goods receipt, invoice and payment documents (their own phases use `NumberRange`), the accounting document numbers of those phases, delivery and billing documents, external number intervals, changing the company codes or plants, real SAP.

## Depends on
`docs/sap/document-numbers.md`, butterfly 21 to 23 (merged).
