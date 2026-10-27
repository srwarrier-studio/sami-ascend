# SAP parity checklist: sales

What SAP users are used to on the sales order screens, and what our web app does about it.
The point is that nobody says "I had this in SAP and it is missing here". Every line is
either built, planned, or deliberately dropped, and the owner of the line is the users.

**Status of this document:** a first draft written from public SAP documentation and general
SAP GUI knowledge, not from the users' own screens. The users confirm it by using the app and
reporting changes. Until a line is confirmed, treat its priority as a proposal.

Sources: SAP Help "Creating a Sales Order" and "Displaying the List of Sales Orders"
(help.sap.com, 4.6C), the MIT VA01 guide (web.mit.edu/CAO/www/SB2002/CR/VA01.htm), the SAP
GUI shortcut reference (experience.sap.com/files/guidelines/References/nv_fkeys_ref2_e.htm),
and SAP community posts on VA05 and ALV layouts.

Priority: **must** (a user will complain), **should** (users will ask for it soon),
**later** (real but not for the first slice), **drop** (intentionally not in the web app).
Status: `built`, `planned` (phase named), `open` (no phase yet).

## 1. Create a sales order (VA01)

SAP flow: initial screen (order type, sales organisation, distribution channel, division,
optional sales office and group), then the overview with a header (sold-to party, ship-to
party, customer reference and date, requested delivery date, payment terms) and an item
table with tabs (item overview, schedule lines, shipping, account assignment).

| SAP behaviour | Priority | Status | Note |
|---------------|----------|--------|------|
| Order type, sold-to party, delivery date, items with material, quantity and unit | must | built | workspace-web 02 |
| Messages listed together, each pointing to its field | must | built | all problems return at once; field errors shown under the field |
| Customer chosen with F4 value help (search by name or number) | must | open | needs a read entity for customers in the contract; typed 10-digit number only today |
| Material chosen with F4 value help (search by number or description) | must | open | same, for materials; description and unit and price fill in after choosing |
| Customer name and material description shown after the number is entered | must | open | SAP shows them next to the field |
| Item table that takes many lines quickly: tab between cells, Enter adds a row, paste several rows from Excel | must | open | the biggest daily-use difference; today one line is added with a button |
| Sales organisation, distribution channel and division | should | open | not in the contract yet; ask the consultants whether one value per user is enough (question to add) |
| Ship-to party (and other partner functions) | should | open | contract has sold-to only |
| Customer reference and reference date | should | open | not in the contract |
| Payment terms, incoterms | later | open | usually defaulted from the customer in SAP |
| Item net price, discounts, taxes shown per line and in the total | should | open | SAP shows pricing after entry; contract returns net amounts only after create |
| Schedule lines and shipping tabs | later | open | |
| Copy from a reference document (create with reference) | should | open | common for repeat orders; needs a read of the source order |
| Save with Ctrl+S, cancel with Esc, F4 opens value help, Enter confirms | must | open | web keyboard map; see section 4 |
| Defaults remembered per user (order type, sales area, currency) | should | open | SAP user parameters; start with order type and currency |
| Order number shown after save with a link to display it | must | built | success banner shows the number; link arrives with the list (workspace-web 03) |
| Incompleteness check: missing fields highlighted before save | should | open | validation runs on save today |
| Long text per header or item | later | open | |
| Attachments | later | open | |
| Account assignment, custom fields | drop | | not part of this business process; add on request |

## 2. Find and list orders (VA05, VA03)

SAP flow: a selection screen (customer, material, document number, order date range, status,
sales area, with "further selection criteria"), then an ALV list. Double-click opens the
order in display mode.

| SAP behaviour | Priority | Status | Note |
|---------------|----------|--------|------|
| List of my recent orders | must | planned | workspace-web 03 |
| Selection by order number, customer, date range, status | must | open | `$filter` already supports these in the contract |
| Open an order in display mode with header, items and status | must | planned | workspace-web 03 |
| Sort by a column; filter by a column | must | open | server side through `$orderby` and `$filter` |
| Column chooser and saved layouts (ALV variants) | should | open | store a layout per user in the app, not in SAP |
| Export the list to Excel | must | open | users will ask for it on day one; CSV first |
| Totals and subtotals by customer or date (ALV summation) | should | open | later through the summary entities |
| Page size and scrolling that handles thousands of rows | should | open | `$top` and `$skip` exist; the table needs paging |
| Status shown as a coloured status (open, in process, completed, cancelled) | must | open | contract has `A`, `B`, `C`, `X`; display names are the web app's job |
| Print | later | open | |
| Selecting several rows and acting on them | later | open | there are no bulk actions in the contract |
| Pre-filled selection from the last search (selection variants) | should | open | |

## 3. Change an order (VA02)

| SAP behaviour | Priority | Status | Note |
|---------------|----------|--------|------|
| Change the requested delivery date of an open order | must | open | butterfly and the contract support it; no screen yet |
| Change items (add, remove, change quantity) | should | open | the contract changes header fields only; ask consultants whether RAP can offer it |
| Cancel or reject an order | should | open | not in the contract |
| Warn when someone else changed the order (SAP locks the document) | must | open | the contract uses an ETag; the screen must say "changed by someone else, reload" |
| Change history (who changed what) | later | open | |

## 4. Behaviour that applies to every screen

| SAP behaviour | Priority | Status | Note |
|---------------|----------|--------|------|
| Keyboard first: Tab order follows the screen, Enter does the obvious thing, Ctrl+S saves, F4 opens value help, Esc leaves | must | open | one keyboard map for all apps; documented in `@sami/ui` |
| Value help (F4) on any field that has a list of valid values | must | open | one shared component in `@sami/ui` |
| Required fields marked, errors next to the field and in one list | must | built | |
| Dates and numbers shown in the user's own format (for example 27.10.2026, 1.250,00) | should | open | SAP uses the user's profile; we use the browser locale until users say otherwise |
| Status line with the last message | drop | | replaced by on-page messages |
| Transaction code box (type VA01 to jump) | later | open | a search box over the menu could do the same |
| Favourites and recently used | should | open | menu by role exists; favourites later |
| Several sessions (windows) | drop | | browser tabs do this |
| Session timeout warning before data is lost | should | open | warn before the cookie expires on a form with unsaved data |
| Authorisation: users see only what they may | must | built | menu by role; data access stays in SAP |

## What this means for the build

1. **Shared components first** (they come up in almost every must-have): a searchable value-help
   select, a keyboard-friendly item grid, a data table with sort, filter, column chooser and
   export, and a consistent message list. These belong in `@sami/ui`, in the same theme.
2. **Contract additions to ask the consultants about:** customer and material read entities for
   value help, sales area fields, ship-to, customer reference, pricing on read, cancel and item
   change. Add these to `consultant-questions.md` as they become relevant.
3. **Phases:** workspace-web 03 should grow to cover the must-haves in section 2, and a new phase
   should cover value help and fast item entry in section 1.

## How users report back

Keep each report to one line, tagged with the section and row it belongs to, for example
"1: customer search by name, I type names not numbers". The line then updates the priority and
status here, and becomes an acceptance case in the phase spec.
