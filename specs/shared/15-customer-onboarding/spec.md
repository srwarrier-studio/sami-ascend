# shared/15 customer-onboarding

## Goal
Define how a new customer is onboarded in workspace from the sales person's request to the customer existing in SAP: who asks, who checks, who approves, who creates, what each of them sees on their board, and how SAP's customer is created, so the request flow and the SAP create can be built in small phases.

## Why
Master data is the core area: nothing is sold before the customer exists. Today a sales person can only pick a customer that already exists. The owner wants the whole onboarding to run in workspace with one person responsible at every step and nothing lost between people, using a new customer as the first case. The same pattern then serves new suppliers and new materials.

## Decisions already made by the owner (2026-11-05)
- **Customer first.** Suppliers and materials follow with the same pattern.
- **Master data person, then finance.** The master data person checks the request, finance sets the credit and payment side, then the master data person creates the customer in SAP.
- **Every request always has one person responsible**, shown on that person's board with how long it has waited (the work board of workspace-api 07 and workspace-web 09, parked until this flow exists).

## The flow
1. **Raise.** A sales person raises a customer request (status `requested`). It is the master data person's work.
2. **Check.** The master data person checks it (no duplicate, details complete). They send it on (`checked`, now finance's work) or return it to the sales person with a reason (`returned`).
3. **Credit and terms.** Finance fills in the credit limit and payment terms and approves (`approved`, back to the master data person's work) or returns it with a reason.
4. **Create.** The master data person creates the customer in SAP. The request becomes `created` with the new customer number and the sales person is told; the customer is now in the Customer dropdown on New sales order.
5. **Fix and resend.** A returned request is the sales person's work again; they change it and send it again to step 2 (`requested`).
- **States and who is responsible:** `requested` (master data), `checked` (finance), `approved` (master data), `returned` (the sales person who raised it), `created` (nobody, done), `withdrawn` (the sales person may withdraw an open request; nobody, done).
- **Roles:** `sales` raises; a new role `master-data` checks and creates; finance is the existing `accounts` role. `admin` has no part in the flow (separation of duties).
- **Done is SAP's state:** `created` is only set when SAP returned the customer number.

## Behavior (to build in the follow-up phases)
- **The request** holds: name, search term, country, address (street, postal code, city), language, contact (name, e-mail, phone), tax number, company code, sales organisation and distribution channel, currency, incoterms (optional); from finance: credit limit and payment terms; and the history of every step (who, what, when, reason).
- **Rules:** a sales person sees only their own requests; the master data and finance roles see the requests that are, or were, theirs; a state can only be left by the role responsible for it; a return always carries a reason; a duplicate check by name and country is run at step 2 and shown to the master data person; finance may not change identity fields and the master data person may not change the credit limit or payment terms.
- **Storage:** requests live in workspace-api's own store (SQLite, as the order queue does). SAP is the truth for the customer itself; the request is the truth for the onboarding steps.
- **On the board** (work board, lanes as configuration): sales has "My requests that were returned" (do) and "My requests in progress" (chase); master data has "Customer requests to check" and "Approved, ready to create" (do); finance has "Customer requests for credit and terms" (do).
- **SAP create** (butterfly stands in for SAP): the customer is created as a business partner with the customer roles, company code and sales area data, through SAP's `API_BUSINESS_PARTNER` (V2 until a V4 is confirmed), numbered by SAP's number range, with SAP's refusals returned to the master data person on the request.

## What this phase produces
A document `docs/sap/customer-onboarding.md` with the flow above, the request fields and routes, the board lanes, the new role, and SAP's side: the create API and body, the customer roles, the required fields for each view (general, company code, sales area), number assignment and real number format, SAP's duplicate behavior and refusals, with each rule tagged with its source (an SAP page, a sandbox response) or listed as an assumption to confirm. The sandbox is read only, so create is documented from SAP's pages and definitions and marked as not exercised. It ends with the follow-up plan.

## Acceptance cases
- The flow shows each step, its responsible role, its states and its exits, with the return paths.
- The request fields are listed with which role fills each, and the rules say who may change what.
- SAP's create API is named with its version and 2022 availability, with a create example, the required fields per view and the refusals; the customer number format is a real sample or a question for the consultants, never invented.
- The new role and its effect on `token-verification`, auth-api and admin-web are listed.
- The follow-up plan lists the phases with order and size, and the owner has agreed it before any code phase starts.

## Out of scope
Supplier and material onboarding (they reuse the pattern), changing or blocking existing customers, bank details and tax validation against government services, attachments, SAP MDG, notifications by e-mail or Teams, any code change.

## Depends on
`docs/sap/master-data-mapping.md`, `docs/sap/document-numbers.md`, `docs/sap/standard/api_business_partner-v2/`, workspace-api 07 (the board, parked).
