# butterfly/22 standard-purchase-requisition

## Goal
Butterfly answers the **real SAP purchase requisition API** (`API_PURCHASEREQUISITION_2`, OData V4) at SAP's own URL and in SAP's own format: read, create with items, and a release step driven by one rule table, so workspace can build the first step of procure to pay against the real contract.

## Why
shared 13 (`docs/sap/p2p-mapping.md`, samples in `docs/sap/standard/api_purchaserequisition_2/`) saved the real `$metadata`, list, item and error responses. The owner decided: the flow starts at the requisition, approval is in, SAP is not configured yet so the release rules live in one table with SAP's standard behavior. Version rule: V4 exists, so V4 is mirrored; V2 is not.

## Behavior
- **Service.** `/sap/opu/odata4/sap/api_purchaserequisition_2/srvd_a2x/sap/purchaserequisition/0001/` with `PurchaseReqn`, `PurchaseReqnItem`, `PurchaseReqnAcctAssgmt`, `PurchaseReqnDelivAddress`, `PurchaseReqnItemText`; `$metadata` is the saved real one, byte for byte. Entity sets butterfly holds no data for answer empty collections.
- **Rows** have every property of the real type in the real order and JSON types; held fields are filled, the rest empty as in the sample (`""`, `null`, `false`, `0`). A contract test compares names and types with the saved sample rows.
- **Reads** as the sandbox: `$top`, `$skip`, `$filter`, `$select`, `$orderby`, `$count=true`, `/$count`, `$expand` with the real navigation names (`_PurchaseRequisitionItem`, `_PurReqn`), `@odata.context`, `@odata.metadataEtag`, row `@odata.etag`. `$apply` aggregate refused with the real `SADL_GW/001` message. Errors in the real V4 body: unknown key 404, bad filter 400 `/IWCOR/CX_OD_EXPR_PARSER_ERROR`, bad expand and bad select 400, with the messages in the samples.
- **Create.** `POST PurchaseReqn` with the header (`PurchaseRequisitionType`, default `NB`) and deep-inserted `_PurchaseRequisitionItem`: needs `Material`, `Plant`, `RequestedQuantity`, `BaseUnit` (or `BaseUnitISOCode`), `DeliveryDate`; price, material group, purchasing group and company code default from the material master and the plant. Gives `201` with the created entity: next number from the range starting `10000000` (internal), items `10, 20, ...`, `PurReqnReleaseStatus` and `ProcessingStatus` `N`, `CreatedByUser`, `PurReqCreationDate`. Refusals (unknown material, unknown plant, quantity not above zero, delivery date missing or in the past) use the V4 error body; the exact SAP messages are assumptions, listed in the notes for the consultants.
- **Release rules.** One table `RELEASE_RULES` (document type, plant, net value range from/to, release group, release code, approver role). Standard behavior: a requisition whose rule says no release is released on save; otherwise its items are not released until each code in the rule's chain is given, in order. Status values: not released, release in progress, released, as the `PurReqnReleaseStatus` field. The table is the only place the owner or the consultants change.
- **Release action.** The real service has none, so butterfly offers a clearly custom route outside the standard path: `POST /butterfly/purchase-requisitions/{number}/release` with the release code; refused when the code is not next in the chain, already given, or the requisition is deleted. Not part of the SAP URL space, so nothing breaks when the real system takes over.
- **Change and delete.** `PATCH` of an item quantity requires `RequestedQuantity` and `BaseUnitISOCode` together (real behavior, SAP KBA 3742701); a requisition already ordered or released cannot change quantity. `DELETE` sets `IsDeleted` on an unreleased, unordered item.
- **Store.** New tables and a repository interface for requisitions (domain entity, application use cases `CreatePurchaseRequisition`, `ReleasePurchaseRequisition`, `ChangePurchaseRequisitionItem`, `ListPurchaseRequisitions`, one class each), SQLite and in-memory implementations, the query engine reads its field names from a table like the sales service. Existing suite untouched.

## Acceptance cases
- `$metadata` equals the saved real file; a list row has exactly the saved sample's property names and JSON types.
- Every saved error sample is reproduced (status and message).
- Create returns the next number from `10000000` with item `10`, status `N` and the right defaults; each refusal gives its error.
- A requisition above a rule's value needs its codes in order; a wrong or repeated code is refused; releasing the last code changes the status and `ReleaseIsNotCompleted`.
- A quantity change without the ISO unit is refused; on an ordered item it is refused.
- `$filter` on `PurReqnReleaseStatus` and `ProcessingStatus`, `$expand`, `$count` give the samples' shapes.

## Out of scope
Purchase order, goods receipt, invoice, payment (the next phases), the shopping-cart actions (`EnablePurReqForPurchasing` and the other four answer 501), account assignment with data, attachments, source determination, the V2 requisition service, workspace-api and workspace-web, the real SAP release service (consultants).

## Depends on
shared 13 (merged), butterfly 21 (the engine and layering to follow).
