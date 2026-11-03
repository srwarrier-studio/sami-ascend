# synapse-api/18 widget-access

## Goal
Every catalog category is open to named roles only. A user sees, and can read data for, the widgets of the categories their roles allow, and department users (production, stores, purchase, sales, accounts, quality) can use Synapse, not only management and admin.

## Behavior
- **Access table.** `widget_access.toml` maps each catalog category to the roles that may use it. First table: Sales to sales; Exports to sales; Finance to accounts; Purchase to purchase; Inventory to stores and purchase; Production to production, stores and quality. `management` and `admin` are always allowed everywhere and are not listed.
- **Catalog.** `GET /v1/synapse/catalog` returns only entries the caller's roles allow.
- **Data.** Every widget data route and the board summary answer `403 WIDGET_NOT_ALLOWED` for a widget the caller cannot see, so hiding is not only in the browser. The board summary ignores widgets the caller cannot see instead of failing.
- **Entry gate.** The Synapse routes accept any role in the table or management and admin, replacing the management-or-admin check. A role in no table row and not management or admin gets 403 as today.
- **Check.** `synapse-api check-access` fails when a catalog category has no row or a row names an unknown role.
- Metrics and records routes (used by intent-api) stay management and admin only.

## Acceptance cases
- A `production` user's catalog has only Production widgets; an `accounts` user's only Finance; management and admin see every entry.
- A `production` user reading a Finance widget gets `403 WIDGET_NOT_ALLOWED`.
- A user with two roles sees the union of both.
- The board summary of a mixed board returns sentences only for the topics the caller may see.
- A new category without a row makes `check-access` fail.

## Out of scope
Per-user grants, an admin page for the table, row-level rules, intent-api scenario access.

## Depends on
synapse-api 17.
