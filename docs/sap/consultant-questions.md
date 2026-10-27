# Questions for SAP consultants

Everything we cannot settle ourselves and must ask the SAP consultants. Add a question here
as soon as it comes up, under the document or area it belongs to. When answered, move it to
Answered with the answer and the date, and update the document that depended on it.

## Open

### Sales contract (`sales-contract.md`)
1. Service name, root path and namespace: confirm or replace section 1.
2. Is `OverallStatus` the right source, and are `A`, `B`, `C`, `X` the right codes?
3. Can `TotalNetAmount` and `NetAmount` be returned in the order currency, with pricing done on create?
4. Is `ETag` available on the order through RAP (`LastChangeDateTime` as the etag field)?
5. Can summary CDS views be exposed as read-only entities with the keys in section 2?
6. Is `$top` above 1000 rejected, and `$count` supported on all entities?
7. Do the validation detail codes in section 6 map to RAP messages with a stable `code`?
8. Which orders may a read-only management login see (sales organisation, plant)?
9. Which `SalesOrderType` values are valid on create, and which message code does SAP return for an invalid one? The contract has no detail code for it yet.
10. May a caller send fields that SAP fills in (for example `OverallStatus`)? We reject them with `FIELD_NOT_ALLOWED`; confirm RAP can do the same.

## Answered

None yet.
