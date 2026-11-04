# workspace-web/05 purchase-requisitions

## Goal
Purchase users enter a purchase requisition and follow its release, and approvers release it, in workspace-web, against workspace-api 05.

## Why
First screens of the procure to pay flow, mirroring SAP's order (requisition, then release). It is the slice that shows whether the butterfly contract and the status words feel right before the purchase order is built on them.

## Behavior
- **Menu** (by role, like sales): `Purchase requisitions` and `New requisition` for `purchase`; `Purchase requisitions` for `management` (approver). Routes `/purchase-requisitions`, `/purchase-requisitions/new`, `/purchase-requisitions/$number`.
- **List page:** table of the user's requisitions (number, description, items, total, created, status). Status is a badge from the items: `Not released`, `In release`, `Released`, `Ordered`; a requisition with mixed items shows the least advanced. Paged with the same pager as the sales order list.
- **New requisition page:** description, then one or more item rows (material, plant, quantity, unit, delivery date, optional text), add and remove rows, same form style, field messages and `422 details` mapping as the new sales order page (a field error on `items/0/material` lands on that row's material). On success it opens the new requisition and shows its number. `503` shows "SAP is not reachable, try again" and keeps the form.
- **Detail page:** the requisition's items with their status and the release codes given. For `management`, a **Release** button per item (and one for all items) with a release-code input; the answer updates the page; SAP's refusal is shown as the message under the button.
- Client `PurchaseRequisitionClient` (`list`, `get`, `create`, `release`) in `src/api/`, with a mock for tests, in router context beside `salesOrders`.
- No browser tool is used by the agent; the owner checks the screens.

## Acceptance cases
- A purchase user sees both purchase menu entries; management sees only the list; sales sees neither and `/purchase-requisitions` redirects to not-allowed.
- A valid form posts the body workspace-api expects and opens the new requisition; a `422` shows field messages on the right row; a `503` keeps the form.
- The list shows the status badge for each case (all three codes and ordered) and pages.
- Release shows the new status after the call, and shows SAP's message when refused; a purchase user has no release button.

## Out of scope
Purchase orders and later steps, edit and delete of items, the visual polish of the badges beyond the shared UI kit, offline queue.

## Depends on
workspace-api 05, workspace-web 04.
