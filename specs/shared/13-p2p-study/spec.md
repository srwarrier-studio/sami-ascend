# shared/13 p2p-study

## Goal
Decide, step by step, how SAP runs procure to pay (requisition to payment) and which of SAP's released APIs, documents, statuses and rules carry each step, so butterfly can mirror the real workflow in the real order and workspace can build the screens on top of it. The result is a mapping document and saved real samples; no code changes.

## Why
The owner wants a full procure to pay flow in workspace that mirrors SAP's workflow order exactly. The SAP consultants have not enabled anything, so butterfly stands in for SAP and has to behave like SAP at every step: which document comes first, what each step checks, what number and status it produces, and what it refuses. That behavior has to be written down from SAP's own documentation and API definitions before it is built.

## Decisions already made by the owner (2026-11-04)
- The flow **starts at the purchase requisition**.
- The **approval step is in**. SAP is not configured for it yet; the consultants will set it before this is built, so butterfly holds the release rules in one configuration table filled with SAP's standard behavior and changeable later.
- **Payment: best guess.** First an outgoing payment for one supplier invoice at a time (the manual payment); a payment run for many due invoices is a later phase. Early payment discount is out of the first version. Both are assumptions to confirm with finance.
- **SAP standard** wherever a value is not known: delivered document types, delivered tolerance keys and movement types.

## Behavior
- A document `docs/sap/p2p-mapping.md` with one section per step, in SAP's order:
  1. **Purchase requisition** (SAP transaction ME51N): the API (service, version, entity sets, V4 if one exists for a 2022 system, otherwise V2), the create body with the required fields, the response, the processing and release statuses, who may create it.
  2. **Release (approval)** of the requisition and of the order (ME54N, ME29N): how SAP decides who must approve (release strategy, groups and codes), the release states, how the release is exposed in the API, and the refusal when something is not released.
  3. **Purchase order** (ME21N), including creating it from requisition items: supplier and price determination (info record, contract), schedule lines, the reference back to the requisition, status, the document number range, and what blocks it.
  4. **Goods receipt** (MIGO, movement type 101, reversal 102): the material document, the link to the order item, how the ordered and delivered quantities and the status change, over and under delivery tolerance, stock and the accounting entry it creates.
  5. **Invoice verification** (MIRO): the supplier invoice, the three-way match of order, goods receipt and invoice, SAP's delivered tolerance keys and their defaults, blocked invoices and their reasons, due date and payment terms.
  6. **Payment** (F-53 for one invoice, F110 for a run): which API carries it, the payment document, how it clears the invoice, the status after payment.
- For every step: the document it creates and its number range, what it requires from the previous document, the statuses before and after, the errors SAP gives (with the real code and message where the sandbox shows one), and the standard role that does it (`purchase`, `stores`, `accounts`, and an approver role to be named).
- A **document flow** section: how each document refers to the one before (requisition item to order item to goods receipt to invoice to payment) in the API fields, and the status the earlier document gets when a later one is posted.
- **Real samples** of each service saved under `docs/sap/standard/<service>/` the way `api_salesorder-v4` was saved: `$metadata`, a list, one item, and the error cases the sandbox allows. Only public Hub sandbox sample data is used; the API key is never saved or committed.
- A section of **assumptions**, each marked "to confirm" with who can confirm it (consultants or finance).
- A **follow-up plan**: one butterfly phase per step (service in the standard format, writes, document flow, SAP's checks), then the workspace-api gateway and the workspace-web screens per step, each with a size and the order.

## Acceptance cases
- Every one of the six steps has a section with its API (name, version, 2022 availability), a create example and its response, the required fields, the statuses, the document number and the errors.
- The document flow section links each step to the previous one by named fields, and states what changes on the earlier document.
- The real definitions and samples of every service named are saved in the repository, and none contains a key.
- Every rule is tagged with its source (an SAP page, a note, or a real sandbox response), or listed as an assumption.
- The assumptions list contains the owner's three decisions (release, payment, standard values).
- The owner has agreed the follow-up plan before any code phase starts.

## Out of scope
Any change to butterfly, synapse-api or the web apps; subcontracting, services and limit orders, stock transfers, returns to supplier, supplier quotation (RFQ) and the contract-based flows; payment run and discount (later phases); the real SAP system.

## Depends on
shared 12 (the method and the saved Sales Order samples), butterfly 21 (a worked example of mirroring a standard service).
