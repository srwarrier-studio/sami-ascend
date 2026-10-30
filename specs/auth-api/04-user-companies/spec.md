# auth-api/04 user-companies

## Goal
Each user has the list of companies they may see, and `/me` and the login token carry it, so the apps can offer a company choice later.

## Behavior
- Three fixed companies, ids in the shared `token_verification` package beside `Role` (`Company`): `sabinsa` (Sami Sabinsa Group Company), `neutraceuticals` (Sami Neutraceuticals Private Limited), `organica` (Organica Aromatic). Display names and logos belong to the web apps, not here.
- `User` gets `companies: list[Company]`, stored in a `user_companies` table (userid, company) like `user_roles`. An existing database gets the table on start; existing users have no company until one is set.
- The JWT gets a `companies` claim (list of ids). `TokenVerifier` returns it with the other claims.
- `GET /me` returns `companies` with the roles. A user with no company still signs in; apps show "no company assigned".
- `create-admin` takes `--company` (repeatable; no flag means all three). A new CLI command `set-companies --email <email> --company <id>...` replaces a user's companies (at least one, unknown id is an error). Until the admin endpoints (phase 02) exist the CLI is the only way to set them.
- Setting companies writes an `audit_log` row only once phase 01 (login-audit) exists; this phase adds no audit.

## Acceptance cases
- Creating an admin with `--company organica` stores exactly that; without the flag stores all three.
- `set-companies` replaces the list, rejects an unknown id and an empty list, and fails for an unknown email.
- The token issued at login contains `companies`; verifying it returns them.
- `/me` returns the user's companies; a user with none gets an empty list and can still sign in.
- Starting the app on a database made before this phase creates the table and keeps every user.

## Out of scope
Admin endpoints for companies (phase 02), filtering SAP data by company, company display names and logos, per-company roles (a role applies in every company the user has).

## Depends on
auth-api 00.
