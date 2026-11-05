# butterfly/24 document-numbers

## Goal
Butterfly numbers its documents the way SAP does (families, year dependence, item steps) and shows customer, supplier and sales order numbers in its standard services the way SAP's own standard APIs show them, without leading zeros, through the same conversion SAP uses, so the next P2P documents and every consumer see the strings SAP will give.

## Why
`docs/sap/document-numbers.md` compared butterfly with the sandbox samples. Requisition and material document numbers already match. Sales orders, customers and suppliers are padded to ten digits (`0000100001`) but the real services return `43103`, `17100001`, `17300001`. The purchase order, goods receipt, invoice and payment phases each need a number range and would otherwise invent their own.

## Behavior
- **`NumberRange`** (domain): a start, an end and a `next(taken)` that returns a higher number than any taken, never reusing one; raises when the interval is full. One instance per family: purchase requisition (from `10000000`), purchase order (`4500000000` to `4599999999`), material document (`4900000000` upward, per year), supplier invoice (`5100000000` upward, per fiscal year), sales order. Year dependent families take the year and restart per year; accounting documents take company code and year.
- **ALPHA conversion at the standard API edge (owner decision, 2026-11-05):** SAP keeps a numeric key padded inside and shows it without leading zeros outside (the conversion exit ALPHA). Butterfly keeps storing customers, suppliers and sales orders padded to ten digits and converts only in its **standard services** (sales order V2 and V4, business partner V2, and the standard requisition service where it carries a customer or supplier number): numeric keys and references are shown without leading zeros (`43103`, `17100001`); on input (the key in a URL, `$filter` comparisons such as `eq`, and values in a create body) either form is accepted and padded before use. Values that are not all digits (`USCU-L-200`) are left as they are. One small helper holds both directions. The older custom services (sales, drivers, finance, inventory, production, exports), their tests, their contract documents and every other app stay unchanged.
- **Items:** requisition, order and sales order items count in steps of 10 (existing behavior stays); material document and invoice items count 1, 2, 3.
- **Gaps:** a number is never reused; the mock does not promise gapless numbers.
- **Consumers:** the apps read the standard services as opaque strings. Tests that compare a standard service's customer or supplier number with the stored padded one are updated. One code change: butterfly's older custom create still requires the stored ten-digit customer number (a deliberate strict rule), so workspace-api pads an all-digit customer number it sends to that create (the form the Customer dropdown now gives is the unpadded one).
- **Next numbers:** the next requisition and the next sales order number come from `NumberRange` (the sales order keeps its ten-digit stored form).

## Acceptance cases
- `NumberRange` gives increasing numbers, skips taken ones, never repeats, and refuses when full; year dependent ranges restart per year.
- In the standard services, sales order, customer and supplier numbers have no leading zeros (keys, references and lists); a key, a `$filter` value or a create body value with leading zeros finds or uses the same record; non-numeric keys are untouched; the old custom services still show the padded form.
- Requisition numbers still start at `10000000`; material documents still show `49…` with `MaterialDocumentYear`.
- A sales order created through the standard service gets the next number of its range and appears in lists and by key without leading zeros.
- The whole butterfly suite passes, and so do the suites of workspace-api, workspace-web, synapse-api and intent-api.

## Out of scope
Purchase order, goods receipt, invoice and payment documents (their own phases use `NumberRange`), the accounting document numbers of those phases, delivery and billing documents, external number intervals, changing the company codes or plants, real SAP.

## Depends on
`docs/sap/document-numbers.md`, butterfly 21 to 23 (merged).
