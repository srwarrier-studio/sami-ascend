# admin-web/01 users

## Goal
A new web app, the admin portal, where admins sign in and manage users. It is the first place a `production` or `accounts` user can be created without touching the database.

## Behavior
- New app `apps/admin-web` (React, Vite, `@sami/ui`, TanStack Router), dev port 5176, its own palette. Same sign-in as the other apps through auth-api; only users with the `admin` role get in (`Not allowed` page otherwise).
- Shell with a menu: Users, Audit log (empty placeholder until admin-web 02).
- **Users page.** Table with name, email, SAP username, roles as badges, companies, status. Search box. Filter by role and by status.
- **Create user.** Form: name, email, SAP username, roles (multi-select from `/roles`), companies (from `/companies`), optional Entra username (when it differs from the email), optional password (leave empty for Entra-only users). Clear messages for duplicate email and weak password.
- **Edit user.** Same fields, plus Disable and Enable with a confirm. The admin sees plain-language help next to each role (what it opens), and a note that production, stores, purchase, sales, accounts and quality users see only their own widgets in Synapse.
- A short note on the form: "Entra proves who they are. What they can open is set here." An Entra-only user shows an `Entra` badge in the table.
- The safety rules of auth-api 02 show as messages, not errors: "You cannot disable yourself", "At least one active admin is needed".

## Acceptance cases
- A non-admin is sent to Not allowed.
- An Entra-only user created here gets exactly the chosen roles when they sign in through Entra; a person with no row is refused.
- Creating a user adds a row; the new user can sign in and gets the chosen roles.
- Editing roles and companies saves and shows in the table.
- Disable asks to confirm; a disabled user is shown greyed with a Disabled badge.
- The last-admin and self-disable cases show their messages.

## Out of scope
Password reset, bulk import, deleting users, the audit log (admin-web 02).

## Depends on
auth-api 02.
