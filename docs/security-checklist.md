# Security & Compliance Checklist

Working checklist for SOC 2 and ISO 27001 readiness. It is a developer aid, not a
certification. Our auditor decides the final control mapping and what evidence they accept.

Tick items when done and record the date and commit in the change log at the bottom.
Anything that is deliberately not done goes in "Accepted risks" with a reason.

## Review cadence

| When | What |
|------|------|
| Every PR | Section 1 (code), no new secrets, tests pass |
| Weekly | Section 2 (CVE scans) |
| Monthly | Sections 3-6 spot check, review access list, review accepted risks |
| Quarterly | Whole checklist, rotate secrets, test restore, review audit-log samples |
| Before each release | Sections 1, 2, 7 |

## 1. Secure coding (every PR)

- [ ] No secrets, tokens or passwords in code, tests, logs or git history
- [ ] All external input validated at the edge (pydantic schemas / DTOs)
- [ ] No SQL built by string concatenation
- [ ] Errors returned to clients are generic; details go only to logs
- [ ] Passwords and tokens never written to logs
- [ ] New route has an auth dependency, and a `require_role` if it is role-restricted
- [ ] New state-changing route is POST/PUT/DELETE, never GET (cookie auth relies on SameSite)
- [ ] Tests added for new auth / permission logic
- [ ] Reviewed by a second person before merge (change management evidence)

## 2. Vulnerability scanning (weekly)

Run from the repo root. Record results and fixes in the change log.

```bash
uv export --frozen --no-hashes --all-packages --no-emit-workspace > /tmp/req.txt
uvx pip-audit -r /tmp/req.txt --disable-pip --no-deps   # Python CVEs
pnpm audit                                              # JS CVEs (run per web app)
uvx bandit -r apps/auth-api/src                         # Python static analysis
```

- [ ] Python dependency CVEs: none open, or each has a ticket and due date
- [ ] JS dependency CVEs: none open, or each has a ticket and due date
- [ ] Bandit: no new High/Medium findings (known ones listed under Accepted risks)
- [ ] Secret scan of repo and history (e.g. `gitleaks detect`)
- [ ] Lock files (`uv.lock`, `pnpm-lock.yaml`) committed and reviewed on change
- [ ] Python and Node runtimes still receive security patches
- [ ] CVE fix SLA followed: Critical 7 days, High 30 days, Medium 90 days (adjust to policy)

## 3. Authentication & session (ISO A.8.5, A.5.17 / SOC 2 CC6.1)

- [x] Passwords hashed with argon2
- [x] Token in httpOnly, Secure, SameSite=Lax cookie
- [x] Tokens are short-lived (`JWT_EXPIRE_MINUTES`)
- [x] Entra login only matches pre-registered users; no auto-creation
- [x] Disabled users cannot log in
- [ ] Login rate limiting / account lockout
- [ ] Password policy: minimum 12 characters enforced on create; breached-password check and password change flow still open
- [ ] MFA for privileged users (admins use Entra login, which enforces MFA, and not password login)
- [ ] Server-side logout / token revocation (today logout only clears the cookie)
- [ ] JWT secret rotation procedure documented and tested
- [ ] Same response and similar timing for unknown user vs wrong password
- [ ] Session/idle timeout agreed with the business

## 4. Authorization & access management (ISO A.5.15, A.5.18, A.8.2 / SOC 2 CC6.2-6.3)

- [x] Role checks enforced in the API, not only hidden in the UI
- [ ] Least privilege: each role reviewed against the pages and APIs it needs
- [ ] Shared SAP login (management) is read-only in SAP, verified
- [ ] SAP service credentials stored in a secret manager, not in the repo or `.env` on servers
- [ ] Admin actions (create user, change role, disable) restricted to `admin` role
- [ ] Joiner / mover / leaver process: access removed on exit, reviewed quarterly
- [ ] Quarterly user and role access review recorded (who reviewed, when)
- [ ] Dev, test and prod users and secrets are separate

## 5. Admin CLI & bootstrap

- [x] Password is prompted (`getpass`), never a command-line argument (shell history, process list)
- [x] No default or hardcoded credentials anywhere
- [x] Goes through the same use case as the admin API (same validation, same hashing); admin API not built yet, it must reuse `CreateUser`
- [x] Writes an audit event with the OS user who ran it
- [x] First-admin bootstrap refuses to run once an admin exists
- [ ] Runs only on the server, by named operators with server access
- [x] User database file is created owner-only (0600)
- [ ] User database is included in backups

## 6. Logging, audit & monitoring (ISO A.8.15, A.8.16 / SOC 2 CC7.2)

- [ ] Audit log records: login success/failure, logout, user created/disabled, role changes, admin CLI use (table exists; only user creation is written so far)
- [ ] Each audit event has who, what, when, source IP, outcome
- [ ] Audit log cannot be edited or deleted through the app
- [ ] Application logs are structured JSON on stdout, with a request id across services (package done, only auth-api uses it so far)
- [ ] No personal data, passwords, tokens or cookies in logs
- [ ] Log retention period defined (commonly at least 12 months for audit logs)
- [ ] Alerting on repeated failed logins and on 5xx spikes
- [ ] Clocks synchronized (NTP) on all hosts

## 7. Transport, configuration & hosting (ISO A.8.9, A.8.24 / SOC 2 CC6.6-6.7)

- [ ] HTTPS everywhere, HTTP redirected; HSTS enabled
- [ ] Security headers on the web app (CSP, X-Content-Type-Options, frame protection)
- [ ] CORS limited to `FRONTEND_URL` (done) and re-checked per environment
- [ ] App not bound to `0.0.0.0` directly on the internet; sits behind a reverse proxy
- [ ] Debug mode and API docs (`/docs`) disabled or protected in production
- [ ] Secrets in a secret manager; `.env` never committed (gitignored, done)
- [ ] Encryption at rest for databases and backups
- [ ] Backups taken, and a restore test recorded
- [ ] Cloud provider chosen and its own compliance reports (SOC 2 / ISO 27001) collected as evidence
- [ ] Network access to SAP limited to the API servers

## 8. Secure development lifecycle (ISO A.8.25, A.8.28, A.8.32 / SOC 2 CC8.1)

- [ ] Protected `main` branch; changes only via reviewed PRs
- [ ] CI runs tests, `pip-audit`, `pnpm audit`, `bandit` and secret scan on every PR
- [ ] Release/deploy steps documented and repeatable
- [ ] Rollback plan for each release
- [ ] Source code access limited to named people (ISO A.8.4)

## 9. Policies & evidence (needed by the auditor, not code)

- [ ] Information security policy
- [ ] Access control policy
- [ ] Incident response plan, with an owner and contact list
- [ ] Vulnerability management policy (the SLA in section 2)
- [ ] Change management policy
- [ ] Business continuity / backup policy
- [ ] Supplier review for cloud, Entra and any third-party services
- [ ] Evidence folder: scan outputs, access reviews, restore tests, PR review history

## Control reference (ISO 27001:2022 Annex A, SOC 2 Trust Services Criteria)

| Topic | ISO 27001:2022 | SOC 2 |
|-------|---------------|-------|
| Access control, rights | A.5.15, A.5.18, A.8.2, A.8.3 | CC6.1-CC6.3 |
| Authentication | A.5.17, A.8.5 | CC6.1 |
| Cryptography | A.8.24 | CC6.1, CC6.7 |
| Logging & monitoring | A.8.15, A.8.16 | CC7.2 |
| Vulnerability management | A.8.8 | CC7.1 |
| Secure development, testing | A.8.25, A.8.28, A.8.29 | CC8.1 |
| Change management | A.8.32 | CC8.1 |
| Config, backup | A.8.9, A.8.13 | CC6.6, A1.2 |
| Supplier / cloud | A.5.19-A.5.23 | CC9.2 |
| Application security reference | OWASP Top 10, OWASP ASVS | - |

## Accepted risks

| Date | Finding | Reason | Review by |
|------|---------|--------|-----------|
| | bandit B104 `0.0.0.0` bind in `entrypoint/app.py` | Needed for containers; must sit behind a reverse proxy (section 7) | Before first deploy |
| | bandit B105 `access_token` | False positive: cookie name, not a password | n/a |

## Change log

| Date | Commit | What was checked or fixed |
|------|--------|---------------------------|
| | | Baseline: `pip-audit` and `pnpm audit` found no known vulnerabilities |
| 2026-10-27 | `7ac8a64` | Logging package: access log has no query string, headers or cookies; httpx URL logging silenced |
