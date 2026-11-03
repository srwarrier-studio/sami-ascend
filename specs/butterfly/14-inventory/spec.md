# butterfly/14 inventory

## Goal
Butterfly serves stock the way SAP will: a new read-only OData V4 service `ZUI_INVENTORY_O4` with stock on hand, goods movements and six summaries, specified in `docs/sap/inventory-contract.md`, with stock that follows from the sales, purchase and production data butterfly already holds.

## Why
The nine Inventory widgets of the catalog (stock value, items below reorder level, availability, stock by warehouse and by material group, slow-moving materials, receipts and issues, reorder list, movement heat map) are fixed numbers in synapse-api's `mock_library.json`. Butterfly is the one source of data and is replaced by SAP later, so stock has to exist there first, as a contract the ABAP team can build from.

## Behavior
- **Contract first.** `docs/sap/inventory-contract.md` (written with this spec) defines the service, `MaterialStock`, `StockMovement` and six summaries with their fields, codes, joins and the SAP sources. The consultant questions 18 to 26 are in `consultant-questions.md`. Every example in the contract is a real response and is checked by a test, like `drivers-contract.md`.
- **Same conventions.** Root `/sap/opu/odata4/sap/zui_inventory_o4/srvd_a2x/sap/zinventory/0001/`, JSON only, the query options, error shapes and paging rules of the other services, `CompanyCode` on every row, read-only, `$expand` refused, one row by key not supported.
- **Master data.** Materials get a `MaterialGroup` (and its name); each company gets a plant and storage locations (a raw material store and a finished goods store, invented names). Both are added to the SQLite tables and the seeds; the sales order and purchase entities do not change.
- **One story.** Stock is generated from what butterfly already knows, so every number can be explained:
  - Goods receipts (`101`) for raw materials are the purchase deliveries, posted on the `ActualDeliveryDate` for the delivered quantity.
  - Goods receipts from production (`131`) for finished products are the production orders, posted on the `ActualEndDate` for the confirmed quantity.
  - Goods issues to production (`261`) are the order components, posted on the production order's end date.
  - Goods issues for deliveries (`601`) are the quantities of the sales order items that are not cancelled, posted on the requested delivery date (the order date when there is none).
  - Opening stock at the start of the history is chosen, deterministically, so stock never goes below zero; current stock is opening plus receipts minus issues. Valuation prices come from the material price lists (raw materials at their purchase price, products at a fixed share of the sales price); `StockValue` is quantity times price, in the company's currency.
  - Reorder levels come from average monthly issues, so a few materials are low or at zero by construction and the same seed gives the same stock.
  - Posting hour comes from the document number, between 08:00 and 17:59 on working days.
- **Tables and views.** New tables `material_group`, `storage_location`, `material_stock`, `stock_movement` and a month-end valuation table; `StockSummaryBy*` and `StockMovementSummaryBy*` are SQL views (one `.sql` file each, like butterfly 13); `StockValueByMonth` reads the valuation table. `StockStatus` is derived in the view, not stored.
- **Existing services do not change.** Nothing already served changes shape; the 1,033 butterfly tests keep passing.

## Acceptance cases
- Every field of every entity matches the contract tables (names, types, nullability); the contract examples match the real responses.
- For every material and location: stock now = opening + receipts − issues, never negative; the sum of `StockValue` of `MaterialStock` equals the last row of `StockValueByMonth` for the same currency and company.
- Receipts of raw materials equal the delivered quantity of `PurchaseDelivery` on its `ActualDeliveryDate`; issues for deliveries equal the item quantities of non-cancelled sales orders.
- `StockStatus` is `Z` exactly when `StockQuantity` is zero, `L` when it is above zero and below `ReorderLevel`, otherwise `O`; `$filter=StockStatus ne 'O'` returns the same rows as comparing in code.
- Each summary equals a hand total over its source rows, for a `CompanyCode` filter too.
- `StockMovementSummaryByHour` has `PostingHour` between 8 and 17, and its counts add up to the movements.
- `BUTTERFLY_SEED=small` serves an empty inventory service (like the drivers service); an unknown entity is `404` in the usual shape.
- Starting butterfly on an existing database adds the inventory data when it is missing and keeps what is there.

## Out of scope
The synapse-api and web widgets (synapse-api 12), purchase spend by material group (butterfly 15, it only needs the group added here), quality and blocked stock, stock transfers between locations, serial and batch numbers, writes, authentication.

## Depends on
butterfly 13 (SQLite store).

## Open questions for the owner
1. Is "warehouse" a storage location of a plant for the real system (the contract assumes so; question 19 asks the consultants)?
2. Do you want movements as value (what the contract has: `ReceiptValue`, `IssueValue`) or as quantity for the "Receipts and issues" chart? Quantities of different materials are in different units and cannot be added, so the contract uses value.
