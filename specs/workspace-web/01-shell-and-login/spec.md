# workspace-web/01 shell-and-login

## Goal
workspace-web has an app shell, a login page and a menu that shows only what the user's roles allow.

## Behavior
- **Pages:** `/login`, `/` (home, welcome and menu), `/not-allowed`. Other paths show a "page not found" message inside the shell. Routing uses TanStack Router (code-based routes, no file generator). A `beforeLoad` guard on each route does the signed-out and role redirects.
- **Session:** on load the app calls `GET {AUTH_URL}/v1/auth/me` with credentials. `200` gives `{ userid, sap_username, roles }`; `401` means signed out. While waiting, show a loading state, not the login page.
- **Signed out:** every page except `/login` redirects to `/login`.
- **Login page:**
  - Username and password form posts to `POST /v1/auth/login/password` as form data (`username`, `password`). `200` then loads `/me` and goes to `/`. `401` shows "Incorrect username or password".
  - "Sign in with Microsoft" is a link to `{AUTH_URL}/v1/auth/login/entra`.
  - `/login?error=entra` shows "Microsoft sign-in failed. Ask an admin to check your account."
  - A signed-in user opening `/login` goes to `/`.
- **Shell:** header with app name, user's `sap_username`, a "Sign out" button (`POST /v1/auth/logout`, then `/login`), and the menu.
- **Menu by role:** one entry table in one file: label, path, allowed roles. Phase 01 has a single entry, "Sales orders" (`/sales-orders`, role `sales`), shown only to users with `sales`. The page itself arrives in workspace-web 02-03; until then the path shows "Coming soon". `admin` has no special menu rights here.
- **Guard:** opening a path whose entry the user's roles do not allow goes to `/not-allowed`, which says what happened and links home.
- **Config:** `VITE_AUTH_URL` (default `http://localhost:8001`). Requests use `credentials: "include"`. API code lives in one `api/auth.ts`; components never call `fetch`.
- **Cookie note:** auth-api sets the cookie `Secure`. Browsers accept it on `http://localhost`; any other dev host needs HTTPS.
- **UI:** components, layout (`AppShell`, `Stack`, `Group`, `Container`, `Title`, `Text`, `TextInput`, `PasswordInput`, `Button`, `NavLink`, `Alert`, `Loader`) and the provider come from `@sami/ui`; wrap the app in `UiProvider` with `workspacePalette`. No `@mantine/*` imports and no inline styles in app code. Add a test that enforces both, like the one in `@sami/ui`.
- **Dependencies:** `@tanstack/react-router` (runtime), `@sami/ui` (workspace). Dev: `vitest`, `@testing-library/react`, `@testing-library/user-event`, `jsdom`, as already used in `@sami/ui`; reuse its `tests/setup.ts` stubs (matchMedia, ResizeObserver). Record them in `tech-stack.md`.
- Charts are not used in this phase.
- Strip the Vite starter files (logo, hero image, counter CSS).

## Acceptance cases
Tests use a fake auth client; no network.
- Loading state shows until `/me` answers.
- `/me` `401` redirects `/` and `/sales-orders` to `/login`.
- Login with good credentials loads `/me` and lands on `/`; `401` shows the error and stays.
- `?error=entra` shows the Microsoft message.
- Signed-in user on `/login` goes to `/`.
- Menu shows "Sales orders" for `sales`, also with other roles; hidden for `admin` alone and for `stores`.
- A user without `sales` opening `/sales-orders` lands on `/not-allowed`.
- Sign out calls logout and lands on `/login`.
- Unknown path shows "page not found" inside the shell.

## Out of scope
Registration, password reset, token refresh, session-expiry handling while the app is open, the sales order pages (02, 03), theming and dark mode, translations, e2e browser tests, route code-splitting.

## Depends on
auth-api 00 (done: `/me`, login, logout, Entra redirect) and shared 06 ui-kit (done).
