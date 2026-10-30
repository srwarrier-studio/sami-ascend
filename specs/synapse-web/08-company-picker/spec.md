# synapse-web/08 company-picker

## Goal
After signing in a user chooses which of their companies they are looking at, can switch company from the header, and the exported PDF carries that company's name and logo.

## Behavior
- `User` gets `companies: string[]` from `/me` (auth-api 04). `MockSessionClient` users get companies too: `manager@` two, `admin@` all three, `sales@` one.
- A `companies.ts` file maps each id to what the app shows: `sabinsa` Sami Sabinsa Group Company, `neutraceuticals` Sami Neutraceuticals Private Limited, `organica` Organica Aromatic. Each has a placeholder logo, a coloured square with the first letter of the name (a later change swaps in real logo files). An id the app does not know is dropped from the user's list.
- The chosen company is kept per user in `localStorage` (`synapse.company.<userid>`) and checked against the user's companies on every start; a stale or unknown value is ignored.
- What happens after sign-in:
  - one company: it is chosen automatically, no picker;
  - several and none chosen: the user lands on `/company`, a full-screen page (no shell, like AI Mode) titled `Choose a company` with one card button per company showing logo and name; clicking one chooses it and opens the boards;
  - none: a page says `No company assigned. Ask an administrator.` with a sign-out button.
- Every other page redirects to `/company` until a company is chosen. `/company` redirects to the boards when the user has one company.
- The header shows the chosen company's logo and name; users with several companies also get a `Switch company` button there that opens `/company` again. `AppFrame` gets an optional `headerExtra` slot for this (shared `@sami/ui`, one prop, other apps unchanged).
- The router context carries `company` (the chosen id) and `setCompany`. The company does not yet filter data or boards: every company shows the same synapse-api data until the later company-data phase.
- The PDF header uses the chosen company's name and logo in place of the `companyBrand` placeholder, which is removed.

## Acceptance cases
- Session: `/me` companies reach the user; unknown ids are dropped.
- One company: signs in straight to the boards, no `Switch company` button, header shows that company.
- Several companies, none chosen: lands on `/company` with a card for each; choosing one opens the boards, shows it in the header and remembers it after a reload.
- `Switch company` returns to the picker; choosing another changes the header.
- A stored company the user no longer has is ignored and the picker shows.
- No company: the "No company assigned" page with sign out; boards are not reachable.
- Another page opened directly before choosing redirects to `/company`.
- Export: the PDF frame header shows the chosen company's name and logo.

## Out of scope
Filtering SAP data or boards by company, real logo files, remembering the choice on the server, choosing the company on the login form, the AI Mode page header.

## Depends on
auth-api 04, synapse-web 07.
