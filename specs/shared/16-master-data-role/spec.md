# shared/16 master-data-role

## Goal
A new role `master-data` exists across the platform, so an admin can give it to the person who checks and creates master records, and the token carries it.

## Why
The customer onboarding flow (shared 15) makes the master data person responsible for checking a request and creating the customer in SAP. Finance is the existing `accounts` role; the master data person has no role yet. The role must exist before any screen or route can name it.

## Behavior
- `Role` in `packages/token-verification` gains `MASTER_DATA = "master-data"`. A token with the role verifies; a token with an unknown role is still refused.
- auth-api stores and returns it like any role: the admin user form lists it, a user can be created or changed with it, and it appears in the user's token. No change to the database layout (roles are stored as text).
- admin-web shows it in the roles list with a one-line help text: "Checks and creates customer, supplier and material records in workspace." The other roles keep their text.
- Synapse does not change: `master-data` alone does not open Synapse (`canUseSynapse` stays as it is).
- `admin` still has no part in master data (separation of duties).

## Acceptance cases
- A token carrying `master-data` verifies and gives `Role.MASTER_DATA`; a require-roles check for it passes for that token and refuses others.
- auth-api creates and updates a user with `master-data`, lists it in the roles endpoint, and the login token carries it.
- admin-web shows the `master-data` checkbox with its help text and saves it.
- A user with only `master-data` cannot use Synapse.
- All tests of the three packages pass.

## Out of scope
Any workspace screen or route for the role (the customer request phases), Synapse widget access for the role, changing existing roles.

## Depends on
shared 15 (the flow that needs the role).
