# butterfly/15 purchase-categories

## Goal
Butterfly serves purchase spend by material group, `PurchaseSummaryByMaterialGroup`, in the drivers service, so the two Purchase category widgets can read real numbers.

## Why
`pur-categories` (spend by category) and `pur-by-category-month` (spend by category per month) were left on fixed numbers in synapse-api 11 because the purchase contract had no material group. Butterfly 14 added material groups as master data, so the summary only needs to join the purchase items to them.

## Behavior
- **Contract.** `docs/sap/drivers-contract.md` gets the entity `PurchaseSummaryByMaterialGroup` (key `OrderDate`, `MaterialGroup`, `Currency`, `CompanyCode`; fields `MaterialGroupName`, `TotalNetAmount`, `OrderCount`) next to the other purchase summaries, with a real example, and a line in the notes for the consultant (aggregate CDS view over the `PurchaseDelivery` view joined to the material group, `MARA-MATKL`). A purchase counts on the day it was ordered; cancelled (`X`) items are left out; items whose material has no group are left out.
- **Same conventions.** Same query options, paging and error rules as the other purchase summaries.
- **Store.** A SQL view in `infrastructure/sqlite/views/PurchaseSummaryByMaterialGroup.sql` over `purchase_delivery`, `material_group_of` and `material_group`; an in-memory version for the test doubles that takes the same group lookup.
- Nothing already served changes.

## Acceptance cases
- For every day, the rows of `PurchaseSummaryByMaterialGroup` add up to the row of `PurchaseSummaryByDay` of the same day, currency and company (every raw material has a group).
- The database and the in-memory version answer the same for filters on group, date, company and amount, ordering and paging.
- A summary row equals a hand total from the `PurchaseDelivery` rows of that group and day.
- The contract example is exactly what the service returns.

## Out of scope
The synapse-api widgets (synapse-api 13), groups for sales, any change to existing entities.

## Depends on
butterfly 14 (material groups).
