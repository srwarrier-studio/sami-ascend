# The standard purchase requisition service in butterfly

Butterfly answers the real `API_PURCHASEREQUISITION_2` (OData V4) at
`/sap/opu/odata4/sap/api_purchaserequisition_2/srvd_a2x/sap/purchaserequisition/0001/`, from the real
`$metadata` and the sandbox samples saved in `docs/sap/standard/api_purchaserequisition_2/`. Study and
sources: `docs/sap/p2p-mapping.md`.

## What is mirrored
- Reads: `PurchaseReqn` and `PurchaseReqnItem` with every real property, `$top`, `$skip`, `$count`, `$filter`,
  `$select`, `$orderby`, `$expand` (`_PurchaseRequisitionItem`, `_PurReqn`), keys, `/$count`, and the real
  error bodies for unknown key, bad filter, unknown select, unknown option, bad value and `$apply`.
- Create: `POST PurchaseReqn` with deep-inserted `_PurchaseRequisitionItem`; numbers from `10000000`, items by 10.
- Change: `PATCH` of an item with `RequestedQuantity` and `BaseUnitISOCode` together and an `If-Match`.
- Delete: `DELETE` of an item sets `IsDeleted`.
- The other three entity sets answer empty; the five shopping-cart actions are not implemented.

## What is butterfly's own (no SAP equivalent found)
- **Release.** The real service has no release action. Rules sit in one table, `RELEASE_RULES`
  (`domain/entities/release_rule.py`): requisition type, plant, net value in rupees from and to, release group,
  release codes in order, approver roles. Placeholder values: under 1,00,000 no release (released on save), up to
  10,00,000 code `01`, above that `01` then `02`. Release is evaluated per item.
- `POST /butterfly/purchase-requisitions/{number}/release` with `{"ReleaseCode": "01"}` and optionally
  `"PurchaseRequisitionItem"`. Codes must come in order and cannot be repeated. Status `01` not released, `02` in
  release, `03` released; `ReleaseIsNotCompleted` follows it.
- Who may release (approver roles) is in the table but not checked: butterfly has no sign-in.
- A quantity change before any code is given re-evaluates the strategy; once a code is given, or the item is
  ordered or deleted, it cannot change.

## To confirm with the consultants
1. Required create fields, and the real create response, refusal codes and messages (the sandbox is read only).
   The codes in butterfly (`MATERIAL_UNKNOWN`, `PLANT_UNKNOWN`, `QUANTITY_NOT_POSITIVE`, `DELIVERY_DATE_IN_PAST`,
   `UNIT_INVALID`, `ITEM_NOT_CHANGEABLE`, `RELEASE_REFUSED`) are butterfly's own.
2. The real release strategy: groups, codes, value limits, per header or per item, and the service that releases.
3. The meaning of the release status codes beyond the two seen (`02`, `03`) and the processing status codes beyond `N` and `B`.
4. Material group and purchasing group defaults: butterfly takes the material group from the request (empty if
   absent) and purchasing group `001`.
5. Plants (`1000`, `2000`, `3000`) and purchasing organizations (`1010`, `1020`, `1030`) are placeholders.
