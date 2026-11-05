# workspace-web/06 master-data

## Goal
The requisition form and the sales order form pick material, plant and customer from master data (searchable dropdowns fed by workspace-api 06) instead of asking the user to type them, and the unit follows the material.

## Why
Typing master data invites errors (wrong number, wrong unit) and is not how SAP works. The owner asked for master data to drive the forms (2026-11-05).

## Behavior
- **Client** `MasterDataClient` (`plants`, `materials(q, plant)`, `customers(q)`, `suppliers(q)`) in `src/api/`, with a mock for tests, in router context beside the other clients.
- **`RemoteSelect`**: a searchable dropdown that asks the client after the user stops typing for 250 ms, shows the number and description of each hit, keeps the chosen option when the list changes, and says "No matches" or "Could not load the list" (and lets the user type again) instead of failing silently.
- **Requisition form** (`/purchase-requisitions/new`): plant is a dropdown of the user's plants (loaded once); material is a `RemoteSelect` limited to the row's plant (disabled until a plant is chosen; changing the plant clears the material); the unit is no longer typed: it shows next to the quantity from the chosen material and is sent with the item. Quantity, delivery date and text stay typed.
- **Sales order form** (`/sales-orders/new`): customer is a `RemoteSelect`; each item's material is a `RemoteSelect`; the unit is shown from the material and sent. Order type, currency and delivery date stay as they are.
- Server messages still land on the right field (a refusal on `items/0/material` shows under that dropdown). The forms still work when a list cannot be loaded: the user sees the message and nothing is sent.
- The agent does not use a browser; the owner checks the screens.

## Acceptance cases
- Typing in the material dropdown asks the client once after the pause, with the row's plant, and shows number and description; choosing one fills the row and shows its unit.
- Choosing another plant clears the row's material; the material dropdown is disabled with no plant.
- The submitted body carries the chosen material number, plant and the material's unit, with no typed unit.
- A customer chosen on the sales order form is sent as `sold_to_party`; the material and unit as before.
- A failed list shows the message; a `422` still marks the right dropdown.

## Out of scope
Supplier dropdowns (the purchase order step uses them later), editing existing documents, caching beyond the plants list, visual polish.

## Depends on
workspace-api 06, workspace-web 05, `@sami/ui` `Select`.
