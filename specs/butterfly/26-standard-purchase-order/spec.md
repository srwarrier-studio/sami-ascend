# butterfly/26 standard-purchase-order

## Goal
Butterfly answers and accepts the **real SAP Purchase Order API** (`API_PURCHASEORDER_2`, V4): a purchase order created from released requisition items shows up at once in the purchase figures synapse reads, so one flow (requisition, release, order) changes values in synapse end to end.

## Why
The owner wants one complete procure-to-pay slice that moves numbers in synapse. The purchase figures (by supplier, day, material, material group) are summed from the stored order items (`purchase_delivery`). Butterfly 22 made requisitions; nothing yet turns a released requisition into an order. Mapping and samples: `docs/sap/p2p-mapping.md` section 3, `docs/sap/standard/api_purchaseorder_2/`.

## Behavior
- **Service** at `/sap/opu/odata4/sap/api_purchaseorder_2/srvd_a2x/sap/purchaseorder/0001/`, real `$metadata` served unchanged, entity sets `PurchaseOrder` and `PurchaseOrderItem` filled from the stored order items; every other set answers empty (as butterfly 21 and 22 do). Rows carry every property of the real type; query options, `$expand=_PurchaseOrderItem`, `$count`, errors and the V4 shapes follow the requisition service. A `PurchaseOrderScheduleLine` row per item shows `OpenPurchaseOrderQuantity`.
- **Create:** `POST PurchaseOrder` with a deep insert of `_PurchaseOrderItem`.
  - Header: `PurchaseOrderType` (`NB`), `CompanyCode`, `PurchasingOrganization`, `PurchasingGroup`, `Supplier`, `DocumentCurrency`.
  - Item: either `PurchaseRequisition` + `PurchaseRequisitionItem` (material, quantity, unit, plant, price and currency come from the requisition item and may be overridden by `OrderQuantity` and `NetPriceAmount`), or a direct `Material`, `Plant`, `OrderQuantity`, unit and `NetPriceAmount`.
  - Number from the `PURCHASE_ORDER` number range (10 digits from `4500000001`), items step 10.
  - Refusals in SAP's V4 error shape, one detail per field, nothing saved: unknown supplier, unknown material or plant, plant not in the company code, a requisition item that is not released, already ordered, deleted or does not exist, currency differing from the header, quantity above the open requisition quantity, missing or invalid fields.
  - A retry carrying the same `Idempotency-Key` returns the first order and creates nothing.
- **Effects of a create** (one transaction): the order items are stored with status `O`, the supplier name from master data and the rupee amount; the requisition item becomes `ProcessingStatus B` with `OrderedQuantity`, `PurchasingDocument` and `PurchasingDocumentItem`; the requisition's change time moves. Synapse's purchase summaries include the order on their next read.
- **Delete an item:** `PATCH PurchaseOrderItem` with `PurchasingDocumentDeletionCode L` sets the item cancelled (`X`): it leaves the purchase summaries and the requisition item is open again (`N`, ordered quantity back). `If-Match` with the ETag is required, as in butterfly 22; a stale one gives 412. An item already received cannot be deleted.
- **Release of the order is out:** orders are created released. The sandbox service has no release action; decision recorded in `notes.md` with the upgrade path (a release rule table as for requisitions).
- **Existing orders** (seed and story data) are readable through the new service with `PurchaseRequisition` empty.

## Acceptance cases
- `$metadata` is byte for byte the saved real one; a list row has exactly the property names and JSON types of the saved sample.
- Creating an order from a released requisition item returns 201 with the number, stores the items, sets the requisition item to `B` with the order number, and `/summary` figures for that supplier and day rise by the order amount (same for material and material group).
- Each refusal case above returns the right code and target and saves nothing; ordering the same requisition item twice is refused the second time.
- Deleting an item removes its amount from the summaries and reopens the requisition item; a stale ETag gives 412.
- The same `Idempotency-Key` twice creates one order.
- The whole existing butterfly suite still passes.

## Out of scope
Release of orders, change of quantity or price, schedule line writes, partners and texts, goods receipt (next phase, butterfly 27), invoice, payment, workspace-api and workspace-web (they follow, step by step).

## Depends on
butterfly 22 (requisition), 23 (master data), 24 (number ranges).
