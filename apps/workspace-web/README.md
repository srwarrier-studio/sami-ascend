# workspace-web

Department users' app: sign in, then work from a menu that shows only what their roles allow.

## Run
- `pnpm --filter workspace-web dev` (needs auth-api on port 8001)
- `pnpm --filter workspace-web test`, `pnpm --filter workspace-web build`

## Env vars
- `VITE_AUTH_URL`: auth-api base URL, default `http://localhost:8001`. auth-api sets a `Secure` cookie; browsers accept it on `http://localhost`, any other dev host needs HTTPS.

## Routes
- `/login`: password form and "Sign in with Microsoft". `?error=entra` shows the failure message.
- `/`: home. `/not-allowed`: shown when a role check fails.
- `/sales-orders`: role `sales`; "Coming soon" until workspace-web 02-03.
- Anything else: "Page not found" inside the shell. Signed-out users go to `/login`.

## Adding a menu entry
Add a line to `src/menu.ts` (label, path, roles) and its route in `src/router.tsx` with the same role check.
