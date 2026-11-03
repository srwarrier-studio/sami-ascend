# butterfly/18 document-flow

## Goal
An order entered through the API (workspace) flows through butterfly the way an order flows through SAP: it becomes an invoice and an open receivable, a goods issue that reduces stock and, for a customer abroad, a shipment, so every service shows it at once and workspace behaves like the real application.

## Why
Today only the seed's own orders have downstream documents. An order created through `POST SalesOrder` appears in the sales summaries but never in receivables, stock or exports, so the dashboards and workspace disagree. In SAP the order starts a document flow (delivery, billing, accounting); butterfly stands in for SAP and has to show the same effects. The real SAP does this itself, so none of this is part of the ABAP handover; it is behaviour of the stand-in.

## Behavior
- **Derived documents are a function of the orders.** Invoices, goods issues for deliveries (stock movement `601` and the stock rows that follow from them) and export shipments are computed from all orders, the seed's and the ones created through the API, plus today's date. The inventory and shipment generators of butterfly 14 and 17 and the invoice rule of butterfly 8 are reused unchanged; only their input changes.
- **When it runs.**
  - At start, whenever the seed is (re)built: the derived tables are written from the seed's orders and the stored API orders together.
  - After every successful `POST SalesOrder` and `PATCH SalesOrder` (default SQLite store only): the derived tables are recomputed in the same process before the response is sent. Recomputing takes well under a second for the story seed.
- **What a new order produces**, the same rules as for seed orders:
  - An invoice dated the order date, due after the customer's payment terms; it is open (a receivable) until the customer's usual delay has passed, then cleared on that date.
  - A goods issue (`601`) for each item on the requested delivery date, or the order date when there is none, once that date has come.
  - For a customer outside India, a shipment on the same date, in transit until its arrival date.
  - Cancelled orders produce nothing (the API cannot cancel yet).
- **Stock stays consistent.** The opening stock of the generator is chosen so stock never goes negative; an extra issue can raise the opening entry. That is a simulation shortcut: SAP would block or go negative, butterfly keeps the books balanced. Stock now still equals opening plus receipts minus issues, and the latest month-end value still equals the stock value.
- **Time passing** is handled at start (the seed is already rebuilt for a new day); a server running across midnight updates the derived documents with the next order write or restart.
- **Production and purchases do not change**: they do not depend on sales orders in the story.
- The in-memory repositories (test doubles) are unchanged and have no document flow.

## Acceptance cases
- Create an order for a customer abroad without a delivery date: the invoice exists and is open, the receivables total grows by the order's value, a shipment in transit exists for it, a `601` issue exists for each item, and the day's export summary and stock summaries include it.
- Create a domestic order: invoice and goods issue, no shipment.
- Create an order with a delivery date in the future: invoice, but no goods issue or shipment yet.
- `PATCH` the delivery date of an order that is already shipped: the goods issue and shipment move to the new date (or leave the data when the new date is in the future).
- After any of these, stock equals opening plus receipts minus issues, is never negative, and the latest month-end stock value equals the stock value; invoice numbers are unique.
- Restarting butterfly on the same file keeps the derived documents of API orders; starting on a later day rebuilds the seed and the API orders still have their invoices, issues and shipments.
- Orders created through the API do not change the production service or the purchase summaries.

## Out of scope
Payments entering from outside (the cash entity is the next phase and also derives from invoices), cancelling orders, partial deliveries and invoices, credit memos, other write flows (purchase orders, goods receipts, confirmations), live updates for a server running across midnight without a write.

## Depends on
butterfly 17 (generators for stock and shipments; branch base).
