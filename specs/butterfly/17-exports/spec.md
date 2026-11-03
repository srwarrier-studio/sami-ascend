# butterfly/17 exports

## Goal
Butterfly serves export shipments as SAP will: a read-only OData V4 service `ZUI_EXPORT_O4` with `ExportShipment` and three summaries (by day, destination and transport mode), specified in `docs/sap/export-contract.md`, with shipments that follow from the export sales orders butterfly already holds.

## Why
The seven Exports widgets (shipments, export revenue, revenue trend, top destinations, shipments by mode, shipments in transit, shipments per day) are fixed numbers in synapse-api's `mock_library.json`. About four orders in five in the story data are sold abroad, so butterfly can derive shipments from them, and it has to hold them as a contract the ABAP team can build from.

## Behavior
- **Contract first.** `docs/sap/export-contract.md` (written with this spec) defines the service, `ExportShipment` and three summaries with fields, codes, joins and SAP sources. Consultant questions 34 to 39 are in `consultant-questions.md`. Every example in the contract is a real response checked by a test.
- **Same conventions** as the other services; summaries are SQL views as in butterfly 13 to 16.
- **One story.** A shipment is generated for every order that is not cancelled and whose country is not `IN`:
  - It ships on the order's requested delivery date (the order date when there is none), never in the future.
  - Mode: about 60% sea, 25% air, 15% road, by the order number; transit time by mode (sea 18 to 32 days, air 3 to 6, road 4 to 8) and a small delay on some shipments.
  - Arrival is the expected date plus the delay, and a shipment whose arrival is after today is in transit (no actual arrival).
  - `NetAmount` is the order total in rupees (dollar orders at butterfly's fixed rate of 80), `DocumentAmount` the order total in its own currency.
  - Country names are master data.
- **Tables and views.** New table `export_shipment`, three `.sql` views; an older database is rebuilt (layout version) and keeps API orders.
- **Orders created through the API** (workspace) are not shipments until the seed is rebuilt: shipments, like stock and production, are generated with the seed, not derived live (see notes).
- Nothing already served changes.

## Acceptance cases
- Every field matches the contract tables; the contract examples match on both stores.
- The shipments are exactly the non-cancelled export orders shipped up to today: one per order, the amounts add up to the orders' totals in rupees.
- A shipment is in transit exactly when its arrival date is after today; delivered shipments have an arrival date on or before today.
- The three summaries equal hand totals over the shipments, for a `CompanyCode` filter too; the destination and mode rows add up to the day rows.
- The database and the in-memory lists answer the same for filters, ordering and paging.
- `BUTTERFLY_SEED=small` serves no shipments; an older database is rebuilt keeping API orders.

## Out of scope
The synapse-api widgets (synapse-api 15), freight cost, customs documents, partial shipments, live derivation from orders created after the seed, writes, authentication.

## Depends on
butterfly 16 (branch base, layout version).
