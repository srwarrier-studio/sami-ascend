# auth-api/01 login-audit

## Goal
Every sign-in and every refusal is recorded in `audit_log`, so the admin portal has something to show and security can see who got in.

## Behavior
- One `audit_log` row per event with `at` (UTC), `actor` (email, or the attempted email when unknown), `action`, `target`, `outcome` (`success` or `failed`, as `create_user` already writes) and `detail` (short reason, never a password or token). New column `detail`, added to existing databases without losing rows.
- Actions: `login.password` and `login.entra`. A failed login records `outcome=failed` with `detail` `bad_email`, `unknown_user`, `bad_password`, `disabled` or (Entra) `no_entra_match`. Logout is not recorded: it only clears the cookie, so there is nothing to prove. An Entra error before an email is known (cancelled or failed at Microsoft) is not recorded either.
- The response to the caller stays the same for every failure kind (no hint whether the email exists).
- Writing the row never blocks the login: if the audit write fails the login result is unchanged and the failure is logged.

## Acceptance cases
- A good and a bad password login each add one row with the right outcome and detail.
- A bad login for an unknown email and for a known email look the same to the caller.
- An audit failure does not turn a good login into an error.
- An old database gains `detail` and keeps its rows.

## Out of scope
Reading the log (auth-api 02), retention and archiving, token revocation.

## Depends on
auth-api 00.
