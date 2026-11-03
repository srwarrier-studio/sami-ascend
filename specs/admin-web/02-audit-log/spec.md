# admin-web/02 audit-log

## Goal
Admins read the audit log in the portal: who signed in, who failed, and who changed what.

## Behavior
- **Audit log page.** Newest first, columns time (local, with relative age on hover), actor, action, target, outcome (green `success`, red `failed`) and detail. Loads 50 at a time with "Load more".
- **Filters.** (An `action` ending in `*` is a prefix match, added to auth-api's audit-log route for the quick views.) Actor (text), action (select of known actions), outcome, date range. Filters live in the URL so a view can be shared.
- **Quick views.** Failed sign-ins, Admin changes, Today.
- **Refresh.** A Refresh button and an optional auto-refresh every 30 seconds; the time of the last load is shown.
- **Export.** Download the filtered rows as CSV (up to 5,000 rows).
- Read-only: no edit or delete anywhere. Empty states say what the filter found.
- Application logs of the services (JSON lines on stdout) are not in this page; see the open question in the roadmap.

## Acceptance cases
- Signing in, a failed login and a user change each appear after Refresh, with the right outcome and detail.
- Filters and quick views narrow the list; reloading the page keeps them.
- "Load more" never repeats a row.
- CSV has the same rows as the filtered list and no password or token text.
- A non-admin cannot open the page.

## Out of scope
Live streaming, charts, retention settings, service log files.

## Depends on
admin-web 01, auth-api 02.
