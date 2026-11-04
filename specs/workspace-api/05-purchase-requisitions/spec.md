# workspace-api/05 purchase-requisitions

## Goal
workspace-api offers role-checked routes to create, list, open and release purchase requisitions, behind a gateway that calls butterfly's real `API_PURCHASEREQUISITION_2` service, so workspace-web can show the first procure to pay step end to end.

## Why
butterfly 22 mirrors the standard requisition service and a release route. Nothing consumes it yet. This phase and workspace-web 05 are the first vertical slice of procure to pay (owner decision 2026-11-04); the gateway keeps the SAP details out of the use cases, so pointing it at the real SAP later changes one class.

## Behavior
- **Gateway** `PurchaseRequisitionGateway` (domain): `create(new)`, `list_recent(top, skip, companies)`, `get(number)`, `release(number, code, item)`. Entities `NewPurchaseRequisition`, `PurchaseRequisition`, `PurchaseRequisitionItem`, `PurchaseRequisitionPage` (snake_case fields, the same style as the sales order entities).
- **Implementations:** `ButterflyPurchaseRequisitionGateway` (httpx, V4 JSON of `docs/sap/standard/api_purchaserequisition_2/`, the release call on butterfly's `/butterfly/purchase-requisitions/{number}/release`) and a mock for tests. `SAP_REQUISITION_URL` and `SAP_RELEASE_URL` settings, default to butterfly on port 8003. No queue: if SAP is not reached the route answers `503 SAP_UNAVAILABLE` and the user enters it again (the sales order queue stays for sales orders; revisit when the owner wants it).
- **Routes** under `/v1/workspace`:
  - `POST /purchase-requisitions` (role `purchase`): body `description`, `items[]` with `material`, `plant`, `quantity`, `unit`, `delivery_date`, optional `text`. `201` with the requisition and its items (number, statuses, amounts). Each item's plant must belong to one of the user's companies (`PLANTS_BY_COMPANY` setting, default `INA1: 1000`, `INA2: 2000`, `INA3: 3000`), else `403 COMPANY_NOT_ALLOWED`. SAP's refusals come back as `422 VALIDATION_FAILED` with `details` (`code`, `target`, `message`) like the sales order.
  - `GET /purchase-requisitions?top&skip` (roles `purchase`, `management`): the user's companies only, newest first, with total.
  - `GET /purchase-requisitions/{number}` (same roles): one requisition with items; `404` if missing or in another company.
  - `POST /purchase-requisitions/{number}/release` (role `management` is the approver role until the owner names one): body `release_code`, optional `item`; returns the item statuses. SAP's refusals (not the next code, already released) come back as `422 VALIDATION_FAILED`.
- **Status words** in every response next to SAP's code: `release_status` is `not_released`, `in_release` or `released` from `01`, `02`, `03`; `ordered` is true when the processing status is `B`.
- Release is a decision of the user's role only; which release codes a user may give is not checked (butterfly does not either): assumption, with the consultants.

## Acceptance cases
- A purchase user creates a requisition for a plant of their company; a plant of another company is `403`; a missing role is `403` from the token check.
- SAP's refusal of an unknown material comes back as `422` with the target `items/0/material` (mapped from butterfly's `_PurchaseRequisitionItem/0/Material`).
- The list shows only the user's companies; a requisition of another company is `404`.
- A `management` user releases step by step; a repeated or out-of-order code is `422` with butterfly's message; a `purchase` user is `403`.
- With butterfly stopped the routes answer `503 SAP_UNAVAILABLE`, nothing is lost silently.
- The gateway test runs against butterfly's real app in process (`create_app` with in-memory repositories), not a hand-made response.

## Out of scope
The web screens (workspace-web 05), the sales order queue behaviour for requisitions, purchase orders and the later steps, who may give which release code, attachments, editing and deleting items (later).

## Depends on
butterfly 22 (merged), workspace-api 04 (company claims in the token).
