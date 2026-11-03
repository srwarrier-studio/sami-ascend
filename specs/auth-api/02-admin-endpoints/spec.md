# auth-api/02 admin-endpoints

## Goal
Admins manage users and read the audit log through the API. Today users can only be made with the `create-admin` CLI.

## Behavior
All routes under `/v1/auth/admin`, admin role only (`403` otherwise), every change written to `audit_log`.
- `GET /users` list (id, name, email, SAP username, roles, companies, disabled, created). Query `q` searches name and email.
- `POST /users` create (name, email, SAP username, roles, companies, optional initial password). Weak password and duplicate email keep the existing errors. Without a password the user can only sign in through Entra (auth-api 03 makes that complete); the admin still sets their roles and companies here.
- `PATCH /users/{id}` change name, SAP username, roles, companies or `disabled`. Roles come from the `Role` enum; an unknown role is `422`.
- `GET /roles` and `GET /companies` return the allowed values, so the portal never hard-codes them.
- `GET /audit-log` newest first, paged (`limit` up to 200, `before` cursor), filters `actor`, `action`, `outcome`, `from`, `to`. Read-only; there is no way to edit or delete rows.
- **Entra users are controlled the same way.** Entra only proves who the person is. Roles, companies and disabled status always come from our user table, for password and Entra sign-ins alike. An Entra identity with no row is refused (no automatic accounts, logged `login.entra` / `failed` / `no_entra_match`), a disabled user is refused, and every token carries the roles and companies of the row at sign-in time. Optional `entra_username` on a user for when the Entra name differs from the email (the lookup tries it first, then the email); it must be unique.
- Safety rules: an admin cannot disable or remove the admin role from themselves, and the last active admin can never be disabled or demoted (`409 LAST_ADMIN`). A disabled user's existing token stops working at the next `/me` and cannot sign in again.
- Fields are snake_case (`sap_username`, `entra_username`, `fullname`); errors are `{detail: {code, message}}` (`USER_ALREADY_EXISTS`, `WEAK_PASSWORD`, `LAST_ADMIN`, `SELF_LOCKOUT`, `ENTRA_USERNAME_TAKEN`). The audit `from` and `to` filters are ISO timestamps; paging is `next` = the id to pass as `before`.
- Admin actions are logged as `user.create`, `user.update`, `user.disable`, `user.enable` with the target email and a short `detail` naming what changed (never a password).

## Acceptance cases
- A non-admin gets 403 on every route.
- Create then list shows the user with roles and companies; a duplicate email is refused.
- Changing roles changes the next token that user receives.
- Disabling a user stops their sign-in; enabling restores it.
- An Entra sign-in for a person with no row is refused; with a row, the token has exactly that row's roles and companies; a differing `entra_username` still matches.
- The last active admin cannot be disabled or demoted; an admin cannot disable themselves.
- Audit log paging returns every row once, newest first, and filters combine.

## Out of scope
Password reset email, deleting users, Entra group sync, custom per-user widget grants, revoking tokens already issued (see the security checklist).

## Depends on
auth-api 01.
